# GitHub Repository Assistant using Corrective RAG

An AI-powered application that allows users to **query and understand GitHub repositories using natural language**.  
The system indexes repository code and documentation, retrieves relevant code segments, and generates grounded answers with **file and line citations**.

This project implements **Corrective Retrieval-Augmented Generation (CRAG)** to improve answer accuracy by validating retrieved context and retrying retrieval when the context is not relevant.

---

# Overview

Understanding large codebases can be difficult, especially when developers need to quickly locate specific functionality or understand the architecture of an unfamiliar repository.

This project solves that problem by allowing users to:

- Paste a GitHub repository URL
- Automatically index the repository
- Ask questions about the repository
- Receive answers grounded in the repository code with citations

The system also generates a **repository map** that highlights key files, entry points, and project structure to help users quickly understand the architecture.

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

# Project Structure


github-repository-assistant-crag
│
├── app.py
├── config.py
├── repo_ingest.py
├── rag_engine.py
├── requirements.txt
└── .env


### app.py
Streamlit user interface.

### config.py
Model configuration and application settings.

### repo_ingest.py
Handles repository download, filtering, chunking, and repository mapping.

### rag_engine.py
Implements hybrid retrieval and the CRAG pipeline.

---

# Installation

## Clone the repository


git clone https://github.com/Sahilyadav1909/github-repository-assistant-crag.git

cd github-repository-assistant-crag


---

## Create a virtual environment


python -m venv venv


Activate it:

### Windows

venv\Scripts\activate


### Mac / Linux

source venv/bin/activate


---

## Install dependencies


pip install -r requirements.txt


---

# Environment Variables

Create a `.env` file in the project root.


GROQ_API_KEY=your_groq_api_key_here


This project uses the **Groq API** for LLM inference.

---

# Running the Application

Start the Streamlit application:


streamlit run app.py


The interface will open in your browser.

---

# Usage Guide

## Step 1: Add GitHub repositories

Paste one or more repository URLs into the sidebar.

Example:


https://github.com/fastapi/fastapi


Click **Ingest Repositories**.

---

## Step 2: Ask questions

Once indexing is complete, ask questions such as:

- "Where is request validation implemented?"
- "How does the routing system work?"
- "Which file initializes the application?"

---

## Step 3: Review results

The system returns:

- A natural language answer
- Cited source files
- Line numbers for relevant code

---

# Example Output

Question:


Where is authentication implemented?


Answer:


Authentication logic is implemented in the JWT middleware.

Source:
backend/auth/jwt.py:L42-L78
backend/auth/middleware.py:L10-L25


---

# Technologies Used

- Python
- Streamlit
- LlamaIndex
- Groq LLM API
- FAISS Vector Store
- HuggingFace Embeddings
- BM25 Keyword Search

---

# Limitations

Current version supports:

- Public GitHub repositories
- Repositories of moderate size

Future improvements may include:

- Private repository support
- Persistent vector storage
- Additional programming language parsing
- Improved architecture analysis

---

# Future Improvements

Possible enhancements include:

- Deeper architecture analysis using LLMs
- Advanced repository summarization
- Pull request and issue integration
- Repository comparison tools
- Conversational memory across sessions