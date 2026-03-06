import os
from dotenv import load_dotenv

from llama_index.core import Settings
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

APP_TITLE = "GitHub Repository Assistant using Corrective RAG"

GITHUB_ZIP_URL = "https://api.github.com/repos/{owner}/{repo}/zipball"

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".idea",
    ".vscode",
    ".mypy_cache",
    ".pytest_cache",
}

IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".exe", ".dll", ".so", ".bin", ".db", ".sqlite",
    ".lock"
}

MAX_FILE_SIZE_BYTES = 300_000
MAX_FILES_PER_REPO = 250

GENERIC_CHUNK_LINES = 80
GENERIC_OVERLAP_LINES = 10

MAX_CONTEXT_CHUNKS = 6
TOP_K_PER_REPO = 4
BM25_TOP_K = 4

TREE_MAX_DEPTH = 3
TREE_MAX_LINES = 120

LLM_MODEL = "llama-3.3-70b-versatile"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def validate_env() -> None:
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing. Add it to your .env file.")


def setup_models():
    validate_env()

    llm = Groq(
        model=LLM_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0.1,
        max_tokens=1500,
    )

    embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)

    Settings.llm = llm
    Settings.embed_model = embed_model

    return llm, embed_model