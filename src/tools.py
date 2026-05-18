"""LangChain tool the agent uses to search MITRE ATT&CK techniques via RAG."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings

FAISS_DIR = Path("data/faiss")
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


_STORE: FAISS | None = None

def _get_store() -> FAISS:
    global _STORE
    if _STORE is None:
        embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        _STORE = FAISS.load_local(str(FAISS_DIR), embeddings, allow_dangerous_deserialization=True)
    return _STORE

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
        and a description excerpt for each.
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