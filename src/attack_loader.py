"""Download MITRE ATT&CK Enterprise STIX bundle and load into a local Chroma vector store.

Run once before extracting:
    uv run python -m src.attack_loader
"""

from __future__ import annotations

import json
from pathlib import Path

import requests
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

ATTACK_STIX_URL = (
    "https://raw.githubusercontent.com/mitre/cti/master/"
    "enterprise-attack/enterprise-attack.json"
)
DATA_DIR = Path("data")
STIX_PATH = DATA_DIR / "enterprise-attack.json"
CHROMA_DIR = DATA_DIR / "chroma"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def download_stix() -> dict:
    """Fetch the STIX bundle if not already cached on disk."""
    DATA_DIR.mkdir(exist_ok=True)
    if STIX_PATH.exists():
        print(f"Using cached STIX at {STIX_PATH}")
        return json.loads(STIX_PATH.read_text())

    print(f"Downloading ATT&CK STIX bundle from {ATTACK_STIX_URL} ...")
    resp = requests.get(ATTACK_STIX_URL, timeout=60)
    resp.raise_for_status()
    STIX_PATH.write_text(resp.text)
    print(f"Saved to {STIX_PATH} ({STIX_PATH.stat().st_size // 1024} KB)")
    return resp.json()


def parse_techniques(stix: dict) -> list[Document]:
    """Extract attack-pattern objects into LangChain Documents.

    We keep one Document per technique/sub-technique. The text we embed is the
    name + description (the prose adversary-behavior content); tactics, T-ID,
    and revocation status live in metadata so we can filter and surface them.
    """
    docs: list[Document] = []
    skipped_revoked = 0

    for obj in stix.get("objects", []):
        if obj.get("type") != "attack-pattern":
            continue
        # Skip revoked/deprecated techniques so we don't surface them
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            skipped_revoked += 1
            continue

        # T-ID lives in external_references where source_name == "mitre-attack"
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

        # Embed name + description — name carries strong lexical signal,
        # description carries the behavioral semantics.
        content = f"{name}\n\n{description}"

        docs.append(
            Document(
                page_content=content,
                metadata={
                    "technique_id": tid,
                    "name": name,
                    "tactics": ", ".join(tactics) if tactics else "",
                },
            )
        )

    print(
        f"Parsed {len(docs)} active techniques "
        f"(skipped {skipped_revoked} revoked/deprecated)"
    )
    return docs


def build_vector_store(docs: list[Document]) -> Chroma:
    """Embed documents and persist to disk."""
    print(f"Loading embedding model: {EMBED_MODEL}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    print(f"Embedding {len(docs)} techniques and writing to {CHROMA_DIR} ...")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name="attack_techniques",
    )
    print(f"Done. Stored {store._collection.count()} embeddings.")
    return store


def main() -> None:
    stix = download_stix()
    docs = parse_techniques(stix)
    build_vector_store(docs)


if __name__ == "__main__":
    main()
