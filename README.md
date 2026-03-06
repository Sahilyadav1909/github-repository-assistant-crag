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

# 🧩 Core Components

## Repository Ingestion

The system downloads repositories from GitHub and extracts relevant files for indexing.

During ingestion it filters unnecessary folders such as:

- `.git`
- `node_modules`
- `venv`
- `dist`
- `build`
- `__pycache__`

Implemented in:

```text
repo_ingest.py
```

---

## Code-Aware Chunking

Instead of splitting files randomly, the system uses structure-aware chunking.

For Python files it extracts:

- functions
- classes
- module headers

This ensures that logical code units remain intact during retrieval.

Each chunk stores metadata including:

- repository name
- file path
- start line
- end line

---

## Hybrid Retrieval

The retrieval system combines two approaches.

### Semantic Search

Uses embeddings to find conceptually related code.

### Keyword Search

Ensures exact matching for:

- function names
- class names
- variable names
- configuration keys

Combining both improves retrieval reliability for code-related queries.

---

## Corrective RAG (CRAG)

Traditional RAG sometimes retrieves irrelevant context.

CRAG improves reliability using a correction loop.

Workflow:

1. Retrieve relevant chunks  
2. Evaluate retrieval relevance  
3. Rewrite query if needed  
4. Retrieve again  
5. Generate final answer  

This reduces hallucinations and ensures answers remain grounded in repository code.

---

## Citations

Every response includes source references.

Example:

```text
backend/auth/jwt.py:L42-L78
```

This allows developers to quickly navigate to the relevant section of code.

---

## Multi-Repository Support

Users can index multiple repositories and search:

- within a specific repository
- across all indexed repositories

This enables cross-repository comparisons.

---

# 🖥️ User Interface

The application provides a **Streamlit web interface**.

Users can:

1. Paste GitHub repository URLs  
2. Ingest repositories  
3. Ask natural language questions  
4. View answers with code citations  
5. Explore repository structure  

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
