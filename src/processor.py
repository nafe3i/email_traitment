"""
processor.py — Pipeline RAG pour AUI Email Support System.
"""

from __future__ import annotations
import time
import logging
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
from functools import lru_cache

import chromadb
import requests

from email_detector import EmailDetector, DetectionResult
from storage import Storage
from sanitizer import sanitize_email
from config import settings

logger = logging.getLogger(__name__)

OLLAMA_BASE          = settings.OLLAMA_BASE
EMBED_MODEL          = settings.OLLAMA_EMBED_MODEL
LLM_MODEL            = settings.OLLAMA_LLM_MODEL
CHROMA_PATH          = settings.CHROMA_PATH
COLLECTION_NAME      = "email_support"
CONFIDENCE_THRESHOLD = settings.CONFIDENCE_THRESHOLD
TOP_K                = settings.TOP_K
OLLAMA_TIMEOUT       = settings.OLLAMA_TIMEOUT

CATEGORIES = [
    "inscription_admission", "scolarite_frais", "cours_academique",
    "it_portail", "vie_campus", "bibliotheque", "stage_carriere", "general",
]


class OllamaClient:

    def embed(self, text: str) -> Optional[list]:
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
        except Exception as e:
            logger.error(f"Ollama embed error: {e}")
            return None

    def generate(self, prompt: str, system: str = "") -> Optional[str]:
        try:
            payload = {
                "model":   LLM_MODEL,
                "prompt":  prompt,
                "stream":  False,
                "options": {"temperature": 0.3},
            }
            if system:
                payload["system"] = system
            r = requests.post(
                f"{OLLAMA_BASE}/api/generate",
                json=payload,
                timeout=OLLAMA_TIMEOUT,
            )
            r.raise_for_status()
            return r.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama generate error: {e}")
            return None

    def health(self) -> bool:
        try:
            r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
            return r.status_code == 200
        except Exception:
            return False


class EmailProcessor:

    def __init__(self, gmail_service=None, storage: Optional[Storage] = None):
        self.gmail      = gmail_service
        self.storage    = storage or Storage()
        self.ollama     = OllamaClient()
        self.detector   = EmailDetector(processed_ids=self.storage.get_processed_ids())
        self.chroma     = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.chroma.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def process_email(
        self,
        email_id:   str,
        sender:     str,
        subject:    str,
        body:       str,
        send_reply: bool = False,
    ) -> dict:
        started_at = time.time()
        record: dict = {
            "id":           email_id,
            "sender":       sender,
            "subject":      subject,
            "body_clean":   "",
            "detection":    {},
            "category":     "general",
            "confidence":   0.0,
            "response":     "",
            "sent":         False,
            "error":        None,
            "processed_at": "",
        }

        try:
            # 1. Detection
            detection: DetectionResult = self.detector.detect(email_id, sender, subject, body)
            record["detection"] = detection.to_dict()

            if not detection.should_process:
                reason = "duplicate" if detection.is_duplicate else f"spam:{detection.spam_reason.value}"
                record["error"] = f"skipped:{reason}"
                self._finalize(record, started_at)
                return record

            # 2. Nettoyage
            _, subject_clean, body_clean = sanitize_email(sender, subject, body)
            record["body_clean"] = body_clean
            full_text = f"{subject_clean} {body_clean}"

            # 3. Embedding
            vector = self.ollama.embed(full_text)
            if vector is None:
                record["error"]    = "ollama_embed_failed"
                record["category"] = self._fallback_category(full_text)
                self._finalize(record, started_at)
                return record

            # 4. Recherche ChromaDB
            rag_docs = self._query_chroma(vector, where=None)

            # 5. Categorisation
            category, confidence   = self._categorize(full_text, rag_docs, detection)
            record["category"]     = category
            record["confidence"]   = confidence

            # 6. Generation reponse
            response_docs    = self._query_chroma(vector, where={"category": category})
            record["response"] = self._generate_response(full_text, category, response_docs, detection)

            # 7. Mise en attente de validation humaine (envoi via /emails/{id}/approve)
            if record["response"] and confidence >= CONFIDENCE_THRESHOLD:
                record["suggested_reply"] = record["response"]
                record["status"] = "pending_review"
                logger.info(f"Email {email_id} mis en attente de validation humaine")
            else:
                record["status"] = "no_reply_needed"

            # 8. Indexation ChromaDB
            self._index_email(email_id, full_text, vector, category, sender, subject)
            self.detector.mark_processed(email_id)

        except Exception as e:
            logger.exception(f"Error processing email {email_id}")
            record["error"] = str(e)

        if self.gmail and self._should_mark_read(record):
            from gmail_service import mark_email_as_read
            mark_email_as_read(self.gmail, email_id)

        self._finalize(record, started_at)
        return record

    @staticmethod
    def _should_mark_read(record: dict) -> bool:
        if record.get("status") == "pending_review":
            return False
        err = record.get("error")
        if err is None:
            return True
        if isinstance(err, str) and err.startswith("skipped:"):
            return True
        return False

    def _query_chroma(self, vector: list, where: Optional[dict], n: int = TOP_K) -> list:
        try:
            count = self.collection.count()
            if count == 0:
                logger.warning("ChromaDB : collection vide, RAG non disponible pour cette requête")
                return []

            kwargs = {
                "query_embeddings": [vector],
                "n_results": min(n, count),
            }
            if where:
                kwargs["where"] = where

            results = self.collection.query(**kwargs)
            docs = results.get("documents", [[]])[0]
            meta = results.get("metadatas", [[]])[0]
            dist = results.get("distances", [[]])[0]
            return [
                {"doc": d, "meta": m, "similarity": round(1 - dist, 3)}
                for d, m, dist in zip(docs, meta, dist)
            ]
        except Exception as e:
            logger.warning(f"ChromaDB query error: {e}")
            return []

    def _categorize(self, full_text: str, rag_docs: list, detection: DetectionResult) -> tuple:
        context    = "\n".join(
            f"- [{d['meta'].get('category','?')}] {d['doc'][:200]}" for d in rag_docs
        ) or "Pas de contexte disponible."
        confidence = rag_docs[0]["similarity"] if rag_docs else 0.0

        prompt = (
            f"Tu es un assistant de support universitaire pour AUI, Ifrane, Maroc.\n\n"
            f"Contexte RAG :\n{context}\n\n"
            f"Email - Langue: {detection.language.value}, "
            f"Expediteur: {detection.sender_type.value}, "
            f"Urgence: {detection.urgency.value}\n"
            f"Contenu: {full_text[:600]}\n\n"
            f"Categories: inscription_admission, scolarite_frais, cours_academique, "
            f"it_portail, vie_campus, bibliotheque, stage_carriere, general\n\n"
            f"Reponds UNIQUEMENT avec le nom exact de la categorie."
        )

        result = self.ollama.generate(prompt)
        if result:
            cat = result.strip().lower().replace(" ", "_")
            if cat in CATEGORIES:
                return cat, confidence

        if rag_docs:
            return rag_docs[0]["meta"].get("category", "general"), confidence * 0.7
        return "general", 0.0

    def _generate_response(self, full_text: str, category: str, rag_docs: list, detection: DetectionResult) -> str:
        examples = "\n".join(
            f"---\nQ: {d['doc'][:150]}\nR: {d['meta'].get('answer', '')[:200]}"
            for d in rag_docs if d["meta"].get("answer")
        ) or "Aucun exemple disponible."

        lang_instr    = "Reponds en francais." if detection.language.value == "fr" else "Reply in English."
        urgency_instr = "Email urgent - reconnais l urgence en debut de reponse." if detection.urgency.value == "high" else ""

        prompt = (
            f"Tu es un assistant de support professionnel pour AUI, Ifrane, Maroc.\n"
            f"{lang_instr} {urgency_instr}\n\n"
            f"Categorie: {category} | Expediteur: {detection.sender_type.value}\n\n"
            f"Exemples de reponses similaires:\n{examples}\n\n"
            f"Email recu:\n{full_text[:800]}\n\n"
            f"Genere une reponse professionnelle et precise. Maximum 200 mots."
        )

        result = self.ollama.generate(prompt)
        if result:
            return result

        fallbacks = {
            "fr": f"Bonjour,\n\nNous avons bien recu votre message. Notre equipe vous repondra dans les plus brefs delais.\n\nCordialement,\nSupport AUI",
            "en": f"Dear sender,\n\nThank you for contacting AUI Support. Our team will get back to you shortly.\n\nBest regards,\nAUI Support",
        }
        return fallbacks.get(detection.language.value, fallbacks["en"])

    def _fallback_category(self, text: str) -> str:
        text_lower = text.lower()
        rules = {
            "inscription_admission": ["admission", "inscription", "candidature", "apply", "enroll"],
            "scolarite_frais":       ["frais", "paiement", "bourse", "tuition", "scholarship", "fee"],
            "cours_academique":      ["cours", "notes", "grade", "schedule", "emploi du temps"],
            "it_portail":            ["myaui", "wifi", "password", "portail", "email universitaire"],
            "vie_campus":            ["residence", "cantine", "dorm", "cafeteria", "sport"],
            "bibliotheque":          ["bibliotheque", "library", "lrc", "livre", "book"],
            "stage_carriere":        ["stage", "internship", "emploi", "career", "job"],
        }
        for cat, keywords in rules.items():
            if any(kw in text_lower for kw in keywords):
                return cat
        return "general"

    def _send_reply(self, email_id: str, to: str, subject: str, body: str) -> bool:
        if not self.gmail:
            logger.warning("Gmail service not configured - reply not sent.")
            return False
        try:
            import base64
            from email.mime.text import MIMEText
            msg            = MIMEText(body)
            msg["to"]      = to
            msg["subject"] = f"Re: {subject}"
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            original = self.gmail.users().messages().get(
                userId="me",
                id=email_id,
                format="metadata",
            ).execute()
            thread_id = original.get("threadId", email_id)
            self.gmail.users().messages().send(
                userId="me",
                body={"raw": raw, "threadId": thread_id},
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Gmail send error: {e}")
            return False

    def _index_email(self, email_id: str, full_text: str, vector: list, category: str, sender: str, subject: str) -> None:
        try:
            existing = self.collection.get(ids=[email_id])
            if existing["ids"]:
                return
            self.collection.add(
                ids=[email_id],
                embeddings=[vector],
                documents=[full_text[:500]],
                metadatas=[{"category": category, "sender": sender, "subject": subject[:100]}],
            )
        except Exception as e:
            logger.warning(f"ChromaDB index error: {e}")

    def _finalize(self, record: dict, started_at: float) -> None:
        record["processed_at"]  = datetime.now(timezone.utc).isoformat()
        record["processing_ms"] = int((time.time() - started_at) * 1000)
        self.storage.save_email(record)

    def get_chroma_stats(self) -> dict:
        return {"collection": COLLECTION_NAME, "documents": self.collection.count(), "path": CHROMA_PATH}
