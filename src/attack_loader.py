"""Download MITRE ATT&CK Enterprise STIX bundle and load into a local FAISS vector store.

Run once before extracting:
    uv run python -m src.attack_loader
"""

from __future__ import annotations

import json
from pathlib import Path

import requests
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

ATTACK_STIX_URL = (
    "https://raw.githubusercontent.com/mitre/cti/master/"
    "enterprise-attack/enterprise-attack.json"
)
DATA_DIR = Path("data")
STIX_PATH = DATA_DIR / "enterprise-attack.json"
FAISS_DIR = DATA_DIR / "faiss"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def download_stix() -> dict:
    DATA_DIR.mkdir(exist_ok=True)
    if STIX_PATH.exists():
        print(f"Using cached STIX at {STIX_PATH}")
        return json.loads(STIX_PATH.read_text())
    print(f"Downloading ATT&CK STIX bundle...")
    resp = requests.get(ATTACK_STIX_URL, timeout=60)
    resp.raise_for_status()
    STIX_PATH.write_text(resp.text)
    print(f"Saved ({STIX_PATH.stat().st_size // 1024} KB)")
    return resp.json()


def parse_techniques(stix: dict) -> list[Document]:
    docs: list[Document] = []
    skipped = 0
    for obj in stix.get("objects", []):
        if obj.get("type") != "attack-pattern":
            continue
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            skipped += 1
            continue
        tid = None
        for ref in obj.get("external_references", []):
            if ref.get("source_name") == "mitre-attack":
                tid = ref.get("external_id")
                break
        if not tid:
            continue
        name = obj.get("name", "")
        description = obj.get("description", "")
        tactics = [
            phase["phase_name"]
            for phase in obj.get("kill_chain_phases", [])
            if phase.get("kill_chain_name") == "mitre-attack"
        ]
        docs.append(Document(
            page_content=f"{name}\n\n{description}",
            metadata={
                "technique_id": tid,
                "name": name,
                "tactics": ", ".join(tactics) if tactics else "",
            },
        ))
    print(f"Parsed {len(docs)} active techniques (skipped {skipped} revoked/deprecated)")
    return docs


def build_vector_store(docs: list[Document]) -> None:
    print(f"Loading embedding model: {EMBED_MODEL}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    print(f"Embedding {len(docs)} techniques and writing to {FAISS_DIR} ...")
    FAISS_DIR.mkdir(parents=True, exist_ok=True)
    store = FAISS.from_documents(docs, embeddings)
    store.save_local(str(FAISS_DIR))
    print(f"Done. Saved FAISS index to {FAISS_DIR}")


def main() -> None:
    stix = download_stix()
    docs = parse_techniques(stix)
    build_vector_store(docs)


if __name__ == "__main__":
    main()