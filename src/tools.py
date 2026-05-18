"""LangChain tool the agent uses to search MITRE ATT&CK techniques via RAG."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_DIR = Path("data/chroma")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_store() -> Chroma:
    """Lazy-load the persisted Chroma store once per process."""
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(
            f"Chroma store not found at {CHROMA_DIR}. "
            "Run `uv run python -m src.attack_loader` first."
        )
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
        collection_name="attack_techniques",
    )


@tool
def search_attack_techniques(behavior_description: str) -> str:
    """Search MITRE ATT&CK for techniques matching a described adversary behavior.

    Args:
        behavior_description: A natural-language description of what the adversary
            did, in your own words. For example: "the malware uses PowerShell to
            execute a base64-encoded command downloaded from a remote server".
            Do NOT pass technique IDs or technique names — describe the behavior.

    Returns:
        Top-5 candidate techniques as a formatted string with T-ID, name, tactics,
        and a description excerpt for each. The agent should then decide which (if
        any) actually matches the behavior described in the report.
    """
    store = _get_store()
    results = store.similarity_search(behavior_description, k=5)

    if not results:
        return "No matching techniques found."

    lines: list[str] = []
    for i, doc in enumerate(results, start=1):
        tid = doc.metadata.get("technique_id", "?")
        name = doc.metadata.get("name", "?")
        tactics = doc.metadata.get("tactics", "")
        excerpt = doc.page_content[:400].replace("\n", " ").strip()
        lines.append(
            f"[{i}] {tid} — {name}\n"
            f"    Tactics: {tactics}\n"
            f"    Description: {excerpt}..."
        )
    return "\n\n".join(lines)
