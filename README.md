# 🤖 GitHub Repository Assistant using Corrective RAG

An AI-powered application that allows users to **query and understand GitHub repositories using natural language**.

The system indexes repository code and documentation, retrieves relevant code segments, and generates grounded answers with **file and line citations**.

It implements **Corrective Retrieval-Augmented Generation (CRAG)** to improve answer accuracy by verifying retrieval quality before generating responses.

The project provides a simple **Streamlit interface** where users can paste GitHub repository URLs and explore the codebase interactively.

---

# 🎯 Overview

Understanding a new codebase often requires manually searching through many folders and files.

This project simplifies that process by allowing users to **ask natural language questions about a repository**.

The system performs the following steps:

1. Downloads the repository from GitHub  
2. Extracts useful code and documentation  
3. Splits files into logical code chunks  
4. Creates embeddings for semantic search  
5. Retrieves relevant code segments  
6. Uses **Corrective RAG** to verify retrieval quality  
7. Generates answers grounded in repository code with citations  

---

# Key Features

## Natural Language Code Querying

Users can ask questions about a repository using natural language.

Examples:

- "Where is authentication implemented?"
- "How does the database connection work?"
- "Which file handles API routing?"

The system retrieves relevant code and documentation to generate accurate answers.

---

## Corrective RAG (CRAG)

This project implements **Corrective Retrieval-Augmented Generation**, which improves reliability compared to traditional RAG.

Workflow:

1. Retrieve relevant code chunks
2. Use an LLM grader to evaluate retrieval relevance
3. If retrieval quality is low, rewrite the query
4. Perform retrieval again
5. Generate the final answer using improved context

This correction loop reduces hallucinations and improves answer quality.

---

## Code-Aware Chunking

Python repositories are chunked using the **AST (Abstract Syntax Tree)**.

Instead of splitting text randomly, the system extracts:

- Functions
- Classes
- Module-level imports

This ensures that logical code units remain intact during retrieval.

---

## Precise Citations

Every indexed code chunk stores metadata including:

- Repository name
- File path
- Starting line number
- Ending line number

Answers include citations such as:


backend/auth/jwt.py:L42-L78


This allows users to immediately locate the relevant code in the repository.

---

## Hybrid Search (Vector + Keyword)

The retrieval system combines two search techniques.

### Semantic Search
Uses embeddings to retrieve semantically relevant code.

### Keyword Search (BM25)
Ensures exact matches for:

- Function names
- Class names
- Variables
- Configuration keys

Combining both techniques improves retrieval reliability.

---

## Multi-Repository Support

Users can index multiple repositories simultaneously and choose:

- A specific repository
- Or search across all indexed repositories

This allows comparison between different projects.

---

## Repository Map

The system generates a high-level overview of each repository including:

- Project file tree
- Detected entrypoints
- Important configuration files

This helps users quickly understand the architecture.

---

# System Architecture

The application consists of four main components.

## Repository Ingestion

The repository is downloaded from GitHub and extracted locally.

Files are filtered to remove irrelevant content such as:

- Build artifacts
- Dependency folders
- Binary files

Relevant code and documentation are then processed.

---

## Code Chunking

Files are converted into structured chunks.

Python files use AST parsing to extract:

- Functions
- Classes
- Module headers

Other file types use structured text chunking.

Each chunk is stored with metadata.

---

## Indexing and Retrieval

Chunks are converted into vector embeddings and stored in a vector index.

Retrieval uses a hybrid strategy:

- Vector similarity search
- BM25 keyword search

Results are merged and ranked.

---

## CRAG Pipeline

When a user submits a query:

1. Retrieve top code chunks
2. Use an LLM grader to check relevance
3. If relevance is low, rewrite the query
4. Retrieve again
5. Generate answer using final context

This ensures answers remain grounded in repository code.

---


# 📂 Project Structure

```text
github-repository-assistant-crag
│
├── app.py
│   Streamlit user interface
│
├── config.py
│   Model configuration and API setup
│
├── repo_ingest.py
│   Repository download, parsing, and chunking
│
├── rag_engine.py
│   Retrieval engine and CRAG pipeline
│
├── requirements.txt
│   Python dependencies
│
├── .env
│   API key configuration
│
└── README.md
```

---

# ⚙️ Tech Stack

**Programming Language**

Python

**AI Framework**

LlamaIndex

**LLM Provider**

Groq API

**Vector Database**

FAISS

**Embeddings**

HuggingFace Embeddings

**User Interface**

Streamlit

---

# 🚀 Installation

## Clone the Repository

```bash
git clone https://github.com/Sahilyadav1909/github-repository-assistant-crag.git
cd github-repository-assistant-crag
```

---

## Create Virtual Environment

```bash
python -m venv venv
```

Activate it.

### Windows

```bash
venv\Scripts\activate
```

### Mac/Linux

```bash
source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file.

```bash
GROQ_API_KEY=your_groq_api_key_here
```

Get a Groq API key from:

```text
https://console.groq.com
```

---

# ▶️ Running the Application

Start the Streamlit server:

```bash
streamlit run app.py
```

Open in browser:

```text
http://localhost:8501
```

---

# 🔍 Example Queries

Example questions you can ask:

- Where is authentication implemented?
- Which file initializes the application?
- How are API routes defined?
- Where is the database connection created?
- What does the main entrypoint file do?

---

# ⚠️ Limitations

Current version supports:

- public GitHub repositories
- moderate repository sizes

Very large repositories may take longer to index.

---

# 📈 Future Improvements

Potential enhancements include:

- private repository support
- persistent vector storage
- deeper repository architecture analysis
- GitHub issues and PR understanding
- conversational memory across sessions

---

# 👨‍💻 Author

**Sahil Yadav**

AI / Generative AI Projects
