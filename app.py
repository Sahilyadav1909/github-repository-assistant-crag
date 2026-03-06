import streamlit as st

from config import APP_TITLE, setup_models
from repo_ingest import build_nodes_for_repo
from rag_engine import build_index, answer_query

st.set_page_config(page_title=APP_TITLE, layout="wide")


@st.cache_resource(show_spinner=False)
def load_models():
    return setup_models()


def init_session():
    if "repo_store" not in st.session_state:
        st.session_state.repo_store = {}
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def render_repo_map(repo_map: dict):
    st.markdown(f"### {repo_map['repo_id']}")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Entrypoints**")
        if repo_map["entrypoints"]:
            for item in repo_map["entrypoints"]:
                st.code(item, language="text")
        else:
            st.write("No obvious entrypoints detected.")

        st.markdown("**Key Files**")
        if repo_map["key_files"]:
            for item in repo_map["key_files"]:
                st.code(item, language="text")
        else:
            st.write("No key files detected.")

        st.markdown(f"**Indexed Files:** {repo_map['total_indexed_files']}")

    with col2:
        st.markdown("**Repository Tree**")
        st.code(repo_map["tree"] or "No tree available.", language="text")


def sidebar_ingestion(embed_model):
    st.sidebar.header("Add GitHub Repositories")

    repo_urls_text = st.sidebar.text_area(
        "Paste one or more GitHub repo URLs (one per line)",
        height=180,
        value=""
    )

    if st.sidebar.button("Ingest Repositories", use_container_width=True):
        urls = [u.strip() for u in repo_urls_text.splitlines() if u.strip()]

        if not urls:
            st.sidebar.error("Please enter at least one GitHub repository URL.")
            return

        progress = st.sidebar.progress(0)
        status = st.sidebar.empty()

        for i, url in enumerate(urls, start=1):
            try:
                status.info(f"Processing: {url}")
                repo_id, repo_map, nodes = build_nodes_for_repo(url)
                index_bundle = build_index(nodes, embed_model)

                st.session_state.repo_store[repo_id] = {
                    "repo_map": repo_map,
                    "index_bundle": index_bundle,
                    "node_count": len(nodes),
                }

                st.sidebar.success(f"Indexed {repo_id} ({len(nodes)} chunks)")

            except Exception as e:
                st.sidebar.error(f"{url} -> {e}")

            progress.progress(i / len(urls))

        status.success("Ingestion completed.")


def main():
    init_session()
    llm, embed_model = load_models()

    st.title(APP_TITLE)
    st.caption("Ask questions about GitHub repositories with CRAG, citations, and repo mapping.")

    sidebar_ingestion(embed_model)

    repo_store = st.session_state.repo_store
    repo_ids = list(repo_store.keys())

    tab1, tab2 = st.tabs(["Chat", "Repo Map"])

    with tab1:
        if not repo_ids:
            st.info("Ingest at least one public GitHub repository from the sidebar to start.")
            return

        scope_options = ["All"] + repo_ids
        selected_repo = st.selectbox("Select scope", scope_options)

        user_query = st.text_input(
            "Ask a question about the repository",
            value=""
        )

        if st.button("Ask", use_container_width=True):
            if not user_query.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Retrieving and generating answer..."):
                    result = answer_query(llm, user_query, selected_repo, repo_store)

                st.session_state.chat_history.append({
                    "query": user_query,
                    "result": result,
                    "scope": selected_repo
                })

        if st.session_state.chat_history:
            st.markdown("---")
            st.subheader("Responses")

            for item in reversed(st.session_state.chat_history):
                st.markdown(f"**Question:** {item['query']}")
                st.markdown(f"**Scope:** {item['scope']}")
                st.markdown("**Answer:**")
                st.write(item["result"]["answer"])

                if item["result"]["rewritten_query"]:
                    st.caption(f"CRAG rewritten query: {item['result']['rewritten_query']}")

                if item["result"]["grade_reason"]:
                    st.caption(f"Relevance grader: {item['result']['grade_reason']}")

                st.markdown("**Sources:**")
                if item["result"]["sources"]:
                    for src in item["result"]["sources"]:
                        st.code(src, language="text")
                else:
                    st.write("No sources available.")

                st.markdown("---")

    with tab2:
        if not repo_ids:
            st.info("No repository indexed yet.")
        else:
            for repo_id in repo_ids:
                render_repo_map(repo_store[repo_id]["repo_map"])
                st.markdown("---")


if __name__ == "__main__":
    main()