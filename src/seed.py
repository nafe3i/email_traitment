"""
seed.py — Charge la knowledge base JSON dans ChromaDB.

Usage CLI :
    python seed.py              -> charge sans reset
    python seed.py --reset      -> vide la base puis recharge
"""

from __future__ import annotations
import sys
import json
import logging
import argparse
from pathlib import Path

import chromadb
import requests

sys.path.insert(0, str(Path(__file__).parent))
from processor import CHROMA_PATH, COLLECTION_NAME, EMBED_MODEL, OLLAMA_BASE, OLLAMA_TIMEOUT

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

KB_PATH = Path(__file__).parent.parent / "data" / "knowledge_base"

VALID_CATEGORIES = {
    "inscription_admission", "scolarite_frais", "cours_academique",
    "it_portail", "vie_campus", "bibliotheque", "stage_carriere", "general"
}


def embed(text: str) -> list | None:
    try:
        r = requests.post(
            f"{OLLAMA_BASE}/api/embed",
            json={"model": EMBED_MODEL, "input": text},
            timeout=OLLAMA_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        embedding = data.get("embeddings", [[]])[0]
        if not embedding:
            raise ValueError(f"Ollama a retourné un vecteur vide pour le modèle {EMBED_MODEL}")
        return embedding
    except requests.RequestException as e:
        logger.error(f"Embed request error: {e}")
        return None
    except Exception as e:
        logger.error(f"Embed unexpected error: {e}")
        return None


def _validate_item(item: dict) -> bool:
    """Valide le schema d un item avant indexation dans ChromaDB."""
    required = {"id", "category", "language", "question", "answer"}
    if not required.issubset(item.keys()):
        logger.warning(f"Item manque des champs requis : {required - item.keys()}")
        return False
    if item["category"] not in VALID_CATEGORIES:
        logger.warning(f"Categorie invalide : {item['category']}")
        return False
    if item["language"] not in ("fr", "en", "ar"):
        logger.warning(f"Langue invalide : {item['language']}")
        return False
    return True


def _load_json_file(json_file: Path) -> list:
    """Charge et retourne les items d un fichier JSON."""
    try:
        with open(json_file, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON invalide dans {json_file.name} : {e}")
        return []
    except IOError as e:
        logger.error(f"Impossible de lire {json_file.name} : {e}")
        return []


def _index_item(collection, item: dict) -> bool:
    """Indexe un item dans ChromaDB. Retourne True si indexe, False sinon."""
    doc_id = item["id"]

    existing = collection.get(ids=[doc_id])
    if existing["ids"]:
        logger.debug(f"Deja indexe : {doc_id}")
        return False

    full_text = f"{item['question']} {item['answer']}"
    vector    = embed(full_text)
    if vector is None:
        logger.warning(f"Embedding echoue pour {doc_id}")
        return False

    collection.add(
        ids=[doc_id],
        embeddings=[vector],
        documents=[full_text[:500]],
        metadatas={
            "category": item["category"],
            "language": item["language"],
            "question": item["question"][:200],
            "answer":   item["answer"][:400],
            "tags":     ",".join(item.get("tags", [])),
            "source":   "knowledge_base",
        },
    )
    logger.info(f"✓ {doc_id} [{item['category']}]")
    return True


def load_knowledge_base(reset: bool = False) -> int:
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.info(f"Collection '{COLLECTION_NAME}' supprimee.")
        except Exception as e:
            logger.warning(f"Impossible de supprimer la collection : {e}")

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    json_files = sorted(KB_PATH.glob("*.json"))
    if not json_files:
        logger.warning(f"Aucun fichier JSON trouve dans {KB_PATH}")
        return 0

    loaded = 0
    for json_file in json_files:
        items = _load_json_file(json_file)
        for item in items:
            if not item.get("validated", True):
                continue
            if not _validate_item(item):
                continue
            if _index_item(collection, item):
                loaded += 1

    logger.info(f"Knowledge base chargee : {loaded} nouveaux documents.")
    logger.info(f"Total collection : {collection.count()} documents.")
    return loaded


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Charge la knowledge base AUI dans ChromaDB")
    parser.add_argument("--reset", action="store_true", help="Vider la base avant de recharger")
    args = parser.parse_args()
    load_knowledge_base(reset=args.reset)
