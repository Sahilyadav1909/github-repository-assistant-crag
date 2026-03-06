import json
import re
from typing import Dict, List

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.vector_stores.faiss import FaissVectorStore

from config import MAX_CONTEXT_CHUNKS, TOP_K_PER_REPO, BM25_TOP_K


def simple_tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text.lower())


def build_index(nodes, embed_model):
    sample_vector = embed_model.get_text_embedding("dimension check")
    dim = len(sample_vector)

    faiss_index = faiss.IndexFlatL2(dim)
    vector_store = FaissVectorStore(faiss_index=faiss_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex(
        nodes=nodes,
        storage_context=storage_context,
        embed_model=embed_model,
    )

    bm25_corpus = [simple_tokenize(node.text) for node in nodes]
    bm25 = BM25Okapi(bm25_corpus)

    return {
        "vector_index": index,
        "bm25": bm25,
        "nodes": nodes,
    }


def get_vector_retriever(index_bundle, top_k: int = TOP_K_PER_REPO):
    return index_bundle["vector_index"].as_retriever(similarity_top_k=top_k)


def retrieve_vector_nodes(query: str, index_bundle) -> List[NodeWithScore]:
    retriever = get_vector_retriever(index_bundle, top_k=TOP_K_PER_REPO)
    return retriever.retrieve(query)


def retrieve_bm25_nodes(query: str, index_bundle) -> List[NodeWithScore]:
    bm25 = index_bundle["bm25"]
    nodes = index_bundle["nodes"]

    tokenized_query = simple_tokenize(query)
    if not tokenized_query:
        return []

    scores = bm25.get_scores(tokenized_query)
    top_indices = np.argsort(scores)[::-1][:BM25_TOP_K]

    results = []
    for idx in top_indices:
        score = float(scores[idx])
        if score <= 0:
            continue
        results.append(NodeWithScore(node=nodes[idx], score=score))

    return results


def merge_results(vector_results: List[NodeWithScore], keyword_results: List[NodeWithScore]) -> List[NodeWithScore]:
    merged: Dict[str, NodeWithScore] = {}

    for item in vector_results + keyword_results:
        source = item.node.metadata.get("source", "")
        if source not in merged:
            merged[source] = item
        else:
            old_score = merged[source].score if merged[source].score is not None else 0.0
            new_score = item.score if item.score is not None else 0.0
            if new_score > old_score:
                merged[source] = item

    results = list(merged.values())
    results = sorted(results, key=lambda x: x.score if x.score is not None else 0.0, reverse=True)
    return results[:MAX_CONTEXT_CHUNKS]


def retrieve_nodes(query: str, selected_repo: str, repo_store: Dict) -> List[NodeWithScore]:
    all_results: List[NodeWithScore] = []

    if selected_repo == "All":
        for repo_id, repo_data in repo_store.items():
            vector_results = retrieve_vector_nodes(query, repo_data["index_bundle"])
            keyword_results = retrieve_bm25_nodes(query, repo_data["index_bundle"])
            repo_results = merge_results(vector_results, keyword_results)
            all_results.extend(repo_results)
    else:
        repo_data = repo_store[selected_repo]
        vector_results = retrieve_vector_nodes(query, repo_data["index_bundle"])
        keyword_results = retrieve_bm25_nodes(query, repo_data["index_bundle"])
        all_results = merge_results(vector_results, keyword_results)

    all_results = sorted(
        all_results,
        key=lambda x: x.score if x.score is not None else 0.0,
        reverse=True,
    )

    deduped: Dict[str, NodeWithScore] = {}
    for item in all_results:
        source = item.node.metadata.get("source", "")
        if source not in deduped:
            deduped[source] = item

    return list(deduped.values())[:MAX_CONTEXT_CHUNKS]


def format_context(nodes: List[NodeWithScore]) -> str:
    blocks = []
    for idx, item in enumerate(nodes, start=1):
        meta = item.node.metadata
        source = meta.get("source", "unknown")
        file_path = meta.get("file_path", "unknown")
        start_line = meta.get("start_line", "?")
        end_line = meta.get("end_line", "?")
        text = item.node.text[:2500]

        blocks.append(
            f"[Context {idx}]\n"
            f"Source: {source}\n"
            f"File: {file_path}\n"
            f"Line Range: L{start_line}-L{end_line}\n"
            f"Content:\n{text}"
        )

    return "\n\n".join(blocks)


def unique_sources(nodes: List[NodeWithScore]) -> List[str]:
    seen = set()
    sources = []
    for item in nodes:
        source = item.node.metadata.get("source", "unknown")
        if source not in seen:
            seen.add(source)
            sources.append(source)
    return sources


def grade_retrieval(llm, query: str, nodes: List[NodeWithScore]) -> Dict:
    context = format_context(nodes)

    prompt = f"""
You are a retrieval relevance grader for a GitHub repository assistant.

User question:
{query}

Retrieved context:
{context}

Decide whether the retrieved context is relevant enough to answer the question.

Return ONLY valid JSON in this exact format:
{{
  "relevant": true,
  "reason": "short reason",
  "rewritten_query": "better rewritten query if needed, otherwise empty string"
}}

Rules:
- Set relevant to true only if the context clearly contains the needed code or documentation.
- Set relevant to false if the context is weak, broad, or off-topic.
- If false, rewrite the query to be more precise using file names, class names, function names, or technical keywords.
"""

    raw = llm.complete(prompt).text.strip()

    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        data = json.loads(raw[start:end])
        return {
            "relevant": bool(data.get("relevant", False)),
            "reason": str(data.get("reason", "")),
            "rewritten_query": str(data.get("rewritten_query", "")),
        }
    except Exception:
        return {
            "relevant": True,
            "reason": "Grader parsing failed; proceeding with initial retrieval.",
            "rewritten_query": "",
        }


def generate_answer(llm, query: str, nodes: List[NodeWithScore]) -> str:
    context = format_context(nodes)

    prompt = f"""
You are an AI assistant that answers questions about GitHub repositories.

Answer the user's question using ONLY the provided context.
If the answer is not present in the context, clearly say that the information was not found in the indexed repository content.
Do not invent code, file names, functions, or architecture details.

When referring to evidence, cite using this format:
[file_path:Lstart-Lend]

Use only citations that appear in the provided context metadata.

User question:
{query}

Context:
{context}

Answer:
"""
    return llm.complete(prompt).text.strip()


def answer_query(llm, query: str, selected_repo: str, repo_store: Dict) -> Dict:
    initial_nodes = retrieve_nodes(query, selected_repo, repo_store)
    if not initial_nodes:
        return {
            "answer": "I could not find any relevant repository content for this query.",
            "sources": [],
            "rewritten_query": "",
            "grade_reason": "No context retrieved.",
        }

    grade = grade_retrieval(llm, query, initial_nodes)

    final_nodes = initial_nodes
    rewritten_query = ""

    if not grade["relevant"] and grade["rewritten_query"].strip():
        rewritten_query = grade["rewritten_query"].strip()
        retry_nodes = retrieve_nodes(rewritten_query, selected_repo, repo_store)
        if retry_nodes:
            final_nodes = retry_nodes

    answer = generate_answer(llm, query, final_nodes)
    sources = unique_sources(final_nodes)

    return {
        "answer": answer,
        "sources": sources,
        "rewritten_query": rewritten_query,
        "grade_reason": grade["reason"],
    }