import ast
import io
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

import requests
from llama_index.core.schema import TextNode

from config import (
    GITHUB_ZIP_URL,
    IGNORE_DIRS,
    IGNORE_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    MAX_FILES_PER_REPO,
    GENERIC_CHUNK_LINES,
    GENERIC_OVERLAP_LINES,
    TREE_MAX_DEPTH,
    TREE_MAX_LINES,
)


def parse_github_url(url: str) -> Tuple[str, str]:
    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, url.strip())
    if not match:
        raise ValueError("Invalid GitHub repository URL.")

    owner, repo = match.group(1), match.group(2)
    repo = repo.replace(".git", "")
    return owner, repo


def download_and_extract_repo(url: str) -> Tuple[str, Path, str]:
    owner, repo = parse_github_url(url)
    repo_id = f"{owner}/{repo}"

    api_url = GITHUB_ZIP_URL.format(owner=owner, repo=repo)
    headers = {"User-Agent": "GitHub-Repository-Assistant-CRAG"}

    temp_dir = tempfile.mkdtemp(prefix="repo_ingest_")

    try:
        response = requests.get(api_url, headers=headers, timeout=60)
        if response.status_code != 200:
            raise ValueError(f"Failed to download repo: {repo_id}")

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            zf.extractall(temp_dir)

        extracted_items = list(Path(temp_dir).iterdir())
        if not extracted_items:
            raise ValueError("Repository extraction failed.")

        root_dir = extracted_items[0]
        return repo_id, root_dir, temp_dir

    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def cleanup_temp_dir(temp_dir: str) -> None:
    if temp_dir:
        shutil.rmtree(temp_dir, ignore_errors=True)


def should_skip_file(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORE_DIRS:
            return True

    if path.suffix.lower() in IGNORE_EXTENSIONS:
        return True

    if not path.is_file():
        return True

    try:
        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return True
    except Exception:
        return True

    return False


def safe_read_text(path: Path) -> str:
    encodings = ["utf-8", "latin-1", "utf-16"]
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return ""


def collect_repo_files(root_dir: Path) -> List[Path]:
    files = []
    for path in root_dir.rglob("*"):
        if should_skip_file(path):
            continue
        files.append(path)
        if len(files) >= MAX_FILES_PER_REPO:
            break
    return files


def build_repo_tree(root_dir: Path) -> str:
    lines: List[str] = []

    def walk(current: Path, depth: int):
        if depth > TREE_MAX_DEPTH:
            return

        try:
            children = sorted(
                [p for p in current.iterdir() if p.name not in IGNORE_DIRS],
                key=lambda x: (x.is_file(), x.name.lower())
            )
        except Exception:
            return

        for child in children:
            if len(lines) >= TREE_MAX_LINES:
                return
            prefix = "  " * depth + ("📄 " if child.is_file() else "📁 ")
            lines.append(f"{prefix}{child.name}")
            if child.is_dir():
                walk(child, depth + 1)

    walk(root_dir, 0)
    return "\n".join(lines[:TREE_MAX_LINES])


def detect_entrypoints(files: List[Path], root_dir: Path) -> List[str]:
    candidates = {
        "main.py", "app.py", "server.py", "run.py",
        "manage.py", "wsgi.py", "asgi.py",
        "index.js", "server.js", "app.js",
        "main.ts", "index.ts",
    }
    results = []
    for file in files:
        if file.name in candidates:
            results.append(str(file.relative_to(root_dir)))
    return sorted(results)[:10]


def detect_key_files(files: List[Path], root_dir: Path) -> List[str]:
    names = {
        "README.md", "README.txt", "requirements.txt",
        "pyproject.toml", "setup.py", "package.json",
        "Dockerfile", ".env.example"
    }
    results = []
    for file in files:
        if file.name in names:
            results.append(str(file.relative_to(root_dir)))
    return sorted(results)[:15]


def make_repo_map(repo_id: str, root_dir: Path, files: List[Path]) -> Dict:
    return {
        "repo_id": repo_id,
        "total_indexed_files": len(files),
        "entrypoints": detect_entrypoints(files, root_dir),
        "key_files": detect_key_files(files, root_dir),
        "tree": build_repo_tree(root_dir),
    }


def create_text_node(
    repo_id: str,
    rel_path: str,
    start_line: int,
    end_line: int,
    text: str,
    symbol: str = ""
) -> TextNode:
    metadata = {
        "repo_id": repo_id,
        "file_path": rel_path,
        "start_line": start_line,
        "end_line": end_line,
        "symbol": symbol,
        "source": f"{repo_id}/{rel_path}:L{start_line}-L{end_line}",
    }
    return TextNode(text=text, metadata=metadata)


def chunk_python_code(repo_id: str, rel_path: str, code: str) -> List[TextNode]:
    lines = code.splitlines()
    nodes: List[TextNode] = []

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return chunk_generic_text(repo_id, rel_path, code)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = getattr(node, "lineno", 1)
            end = getattr(node, "end_lineno", start)

            chunk_text = "\n".join(lines[start - 1:end]).strip()
            if not chunk_text:
                continue

            symbol = getattr(node, "name", "")
            nodes.append(
                create_text_node(
                    repo_id=repo_id,
                    rel_path=rel_path,
                    start_line=start,
                    end_line=end,
                    text=chunk_text,
                    symbol=symbol,
                )
            )

    if not nodes:
        return chunk_generic_text(repo_id, rel_path, code)

    header_end = 0
    for item in tree.body:
        if isinstance(item, (ast.Import, ast.ImportFrom)):
            header_end = max(header_end, getattr(item, "end_lineno", 0))

    if header_end > 0:
        header_text = "\n".join(lines[:header_end]).strip()
        if header_text:
            nodes.insert(
                0,
                create_text_node(
                    repo_id=repo_id,
                    rel_path=rel_path,
                    start_line=1,
                    end_line=header_end,
                    text=header_text,
                    symbol="module_imports",
                )
            )

    return nodes


def chunk_markdown(repo_id: str, rel_path: str, text: str) -> List[TextNode]:
    lines = text.splitlines()
    heading_indices = []

    for idx, line in enumerate(lines, start=1):
        if line.strip().startswith("#"):
            heading_indices.append(idx)

    if not heading_indices:
        return chunk_generic_text(repo_id, rel_path, text)

    heading_indices.append(len(lines) + 1)
    nodes: List[TextNode] = []

    for i in range(len(heading_indices) - 1):
        start = heading_indices[i]
        end = heading_indices[i + 1] - 1
        chunk_text = "\n".join(lines[start - 1:end]).strip()
        if chunk_text:
            heading = lines[start - 1].strip()
            nodes.append(
                create_text_node(
                    repo_id=repo_id,
                    rel_path=rel_path,
                    start_line=start,
                    end_line=end,
                    text=chunk_text,
                    symbol=heading,
                )
            )

    return nodes


def chunk_generic_text(repo_id: str, rel_path: str, text: str) -> List[TextNode]:
    lines = text.splitlines()
    nodes: List[TextNode] = []

    if not lines:
        return nodes

    start = 1
    while start <= len(lines):
        end = min(start + GENERIC_CHUNK_LINES - 1, len(lines))
        chunk_text = "\n".join(lines[start - 1:end]).strip()

        if chunk_text:
            nodes.append(
                create_text_node(
                    repo_id=repo_id,
                    rel_path=rel_path,
                    start_line=start,
                    end_line=end,
                    text=chunk_text,
                    symbol="text_chunk",
                )
            )

        if end == len(lines):
            break

        start = end - GENERIC_OVERLAP_LINES + 1

    return nodes


def build_nodes_for_repo(url: str) -> Tuple[str, Dict, List[TextNode]]:
    repo_id = ""
    root_dir = None
    temp_dir = ""

    try:
        repo_id, root_dir, temp_dir = download_and_extract_repo(url)
        files = collect_repo_files(root_dir)
        repo_map = make_repo_map(repo_id, root_dir, files)

        all_nodes: List[TextNode] = []

        for file_path in files:
            rel_path = str(file_path.relative_to(root_dir))
            text = safe_read_text(file_path)
            if not text.strip():
                continue

            if file_path.suffix.lower() == ".py":
                nodes = chunk_python_code(repo_id, rel_path, text)
            elif file_path.suffix.lower() in {".md", ".markdown"}:
                nodes = chunk_markdown(repo_id, rel_path, text)
            else:
                nodes = chunk_generic_text(repo_id, rel_path, text)

            all_nodes.extend(nodes)

        if not all_nodes:
            raise ValueError(f"No usable text/code chunks found for {repo_id}")

        return repo_id, repo_map, all_nodes

    finally:
        cleanup_temp_dir(temp_dir)