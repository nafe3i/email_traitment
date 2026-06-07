"""
api.py — API REST FastAPI pour AUI Email Support System.

Endpoints publics :
  GET    /health
  POST   /auth/login
  POST   /auth/register

Endpoints proteges (JWT requis) :
  POST   /emails/process
  POST   /emails/run
  GET    /emails/history
  GET    /emails/{id}
  GET    /stats
  POST   /seed            (admin)
  DELETE /reset           (admin)
  GET    /users           (admin)
  PATCH  /users/{email}/role  (admin)
  DELETE /users/{email}   (admin)

Lancement :
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import sys
import uuid
import logging
from pathlib import Path
from typing import Optional
from functools import lru_cache

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from processor import EmailProcessor, OllamaClient
from config import settings
from sanitizer import sanitize_email
from storage import Storage
from auth import (
    User, UserCreate, UserLogin, TokenResponse,
    get_current_user, require_role,
    login_user, register_user,
)
from database import (
    get_db, get_all_users, update_user_role,
    deactivate_user, init_db
)

init_db()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_DOMAIN = os.getenv("ALLOWED_REGISTER_DOMAIN", "aui.ma")

# ─── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "AUI Email Support System API",
    description = "API REST pour AUI Email Support System — 100% local, Ollama + ChromaDB.",
    version     = "2.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── Singletons via lru_cache (thread-safe, pas de global mutable) ────────────

@lru_cache(maxsize=1)
def _get_storage() -> Storage:
    return Storage()

@lru_cache(maxsize=1)
def get_processor() -> EmailProcessor:
    return EmailProcessor(gmail_service=None, storage=_get_storage())


# ─── Schemas Pydantic ──────────────────────────────────────────────────────────

class ProcessEmailRequest(BaseModel):
    id:         str  = Field(default_factory=lambda: uuid.uuid4().hex)
    sender:     str  = Field(..., example="student@aui.ma")
    subject:    str  = Field(..., example="Demande de releve de notes")
    body:       str  = Field(..., example="Bonjour, je souhaite obtenir mon releve de notes...")
    send_reply: bool = Field(False)

class RunRequest(BaseModel):
    max_emails: int  = Field(20, ge=1, le=50)
    send_reply: bool = Field(False)

class SeedRequest(BaseModel):
    reset_first: bool = Field(False)


# ─── Auth (publics) ────────────────────────────────────────────────────────────

@app.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
@limiter.limit("5/minute")
def login(request: Request, credentials: UserLogin, db: Session = Depends(get_db)):
    """Login — retourne un JWT token."""
    result = login_user(db, credentials)
    if not result:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    return result


@app.post("/auth/register", response_model=User, tags=["Auth"])
@limiter.limit("3/hour")
def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """Inscription publique — role viewer attribue automatiquement."""
    domain = user_data.email.split("@")[-1].lower()
    if domain != ALLOWED_DOMAIN:
        raise HTTPException(
            status_code=403,
            detail=f"Inscription réservée aux adresses @{ALLOWED_DOMAIN}",
        )
    try:
        return register_user(db, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/auth/me", response_model=User, tags=["Auth"])
def me(current_user: User = Depends(get_current_user)):
    """Retourne les informations de l utilisateur connecte."""
    return current_user


# ─── Users (admin) ─────────────────────────────────────────────────────────────

@app.get("/users", tags=["Users"])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Liste tous les utilisateurs. Admin uniquement."""
    return {"users": get_all_users(db)}


@app.patch("/users/{email}/role", tags=["Users"])
def change_role(
    email: str,
    role:  str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Promouvoir/retrograder un utilisateur. Admin uniquement."""
    if role not in ("admin", "user", "viewer"):
        raise HTTPException(400, "Role invalide. Valeurs : admin, user, viewer")
    if not update_user_role(db, email, role):
        raise HTTPException(404, f"Utilisateur '{email}' non trouve.")
    return {"message": f"Role de {email} mis a jour : {role}"}


@app.delete("/users/{email}", tags=["Users"])
def remove_user(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    """Desactive un utilisateur (soft delete). Admin uniquement."""
    if email == current_user.email:
        raise HTTPException(400, "Vous ne pouvez pas desactiver votre propre compte.")
    if not deactivate_user(db, email):
        raise HTTPException(404, f"Utilisateur '{email}' non trouve.")
    return {"message": f"Utilisateur {email} desactive."}


# ─── System ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Systeme"])
@limiter.limit("60/minute")
def health(request: Request):
    """Verifie l etat du serveur, d Ollama et de ChromaDB."""
    storage = _get_storage()
    return {
        "status":  "ok",
        "ollama":  OllamaClient().health(),
        "chroma":  get_processor().get_chroma_stats(),
        "storage": {"path": str(storage.path), "total": len(storage.get_all())},
    }


@app.get("/stats", tags=["Systeme"])
def get_stats(current_user: User = Depends(get_current_user)):
    """Statistiques globales."""
    storage = _get_storage()
    stats   = storage.get_stats()
    stats["chroma"] = get_processor().get_chroma_stats()
    return stats


@app.post("/seed", tags=["Systeme"])
def seed_knowledge_base(
    req: SeedRequest,
    current_user: User = Depends(require_role(["admin"])),
):
    """Charge ou recharge la knowledge base. Admin uniquement."""
    try:
        from seed import load_knowledge_base
        count = load_knowledge_base(reset=req.reset_first)
        return {"status": "ok", "documents_loaded": count}
    except ImportError:
        raise HTTPException(503, "Module seed non disponible.")
    except Exception as e:
        logger.exception("Seed error")
        raise HTTPException(500, "Erreur lors du chargement de la knowledge base.")


@app.delete("/reset", tags=["Systeme"])
@limiter.limit("1/hour")
def reset_all(request: Request, current_user: User = Depends(require_role(["admin"]))):
    """Reinitialise la base vectorielle et l historique. Admin uniquement."""
    try:
        import chromadb
        from processor import CHROMA_PATH, COLLECTION_NAME
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        client.delete_collection(COLLECTION_NAME)
        client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
        _get_storage().reset()
        get_processor.cache_clear()
        return {"status": "ok", "message": "Base vectorielle et rapport reinitialises."}
    except Exception as e:
        logger.exception("Reset error")
        raise HTTPException(500, "Erreur lors de la reinitialisation.")


# ─── Emails ────────────────────────────────────────────────────────────────────

@app.post("/emails/process", tags=["Emails"])
@limiter.limit("10/minute")
def process_email(
    request: Request,
    req: ProcessEmailRequest,
    current_user: User = Depends(get_current_user),
):
    """Traite un email manuellement via le pipeline RAG."""
    sender, subject, body = sanitize_email(req.sender, req.subject, req.body)
    record = get_processor().process_email(
        email_id   = req.id,
        sender     = sender,
        subject    = subject,
        body       = body,
        send_reply = req.send_reply,
    )
    # Supprimer les champs internes avant de retourner au client
    record.pop("_prompt", None)
    record.pop("_context", None)
    return record


@app.post("/emails/run", tags=["Emails"])
@limiter.limit("5/minute")
def run_gmail(
    request: Request,
    req: RunRequest,
    current_user: User = Depends(require_role(["admin", "user"])),
):
    """Declenche le traitement des emails Gmail non lus."""
    try:
        from gmail_service import get_gmail_service, fetch_unread_emails
    except ImportError:
        raise HTTPException(503, "Module gmail_service non disponible. Configurez Gmail OAuth2.")

    try:
        service = get_gmail_service()
        emails  = fetch_unread_emails(service, max_results=req.max_emails)
    except Exception:
        logger.exception("Gmail fetch error")
        raise HTTPException(500, "Erreur lors de la recuperation des emails Gmail.")

    storage = _get_storage()
    proc    = EmailProcessor(gmail_service=service, storage=storage)
    results = []
    for em in emails:
        record = proc.process_email(
            email_id   = em["id"],
            sender     = em.get("sender", ""),
            subject    = em.get("subject", ""),
            body       = em.get("body", ""),
            send_reply = req.send_reply,
        )
        record.pop("_prompt", None)
        record.pop("_context", None)
        results.append(record)

    return {
        "processed": len(results),
        "sent":      sum(1 for r in results if r.get("sent")),
        "skipped":   sum(1 for r in results if r.get("error", "").startswith("skipped")),
        "results":   results,
    }


@app.get("/emails/history", tags=["Emails"])
@limiter.limit("100/minute")
def get_history(
    request: Request,
    current_user: User = Depends(get_current_user),
    limit:    int           = Query(50, ge=1, le=500),
    category: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
):
    """Retourne l historique des emails traites avec filtres optionnels."""
    emails = _get_storage().get_all()
    if category:
        emails = [e for e in emails if e.get("category") == category]
    if language:
        emails = [e for e in emails if e.get("detection", {}).get("language") == language]
    emails = sorted(emails, key=lambda e: e.get("processed_at", ""), reverse=True)
    return {"total": len(emails), "emails": emails[:limit]}


@app.get("/emails/pending", tags=["Emails"])
def get_pending_emails(current_user: User = Depends(get_current_user)):
    """Liste les emails en attente de validation humaine."""
    if current_user.role not in ("admin", "user"):
        raise HTTPException(status_code=403, detail="Accès refusé")
    return _get_storage().get_pending()


@app.post("/emails/{email_id}/approve", tags=["Emails"])
def approve_email(email_id: str, current_user: User = Depends(get_current_user)):
    """Approuve la réponse générée et l'envoie via Gmail."""
    if current_user.role not in ("admin", "user"):
        raise HTTPException(status_code=403, detail="Accès refusé")

    storage = _get_storage()
    email = storage.get_by_id(email_id)

    if not email:
        raise HTTPException(status_code=404, detail="Email introuvable")
    if email.get("status") != "pending_review":
        raise HTTPException(status_code=400, detail=f"Statut invalide : {email.get('status')}")
    if not email.get("suggested_reply"):
        raise HTTPException(status_code=400, detail="Aucune réponse générée pour cet email")

    gmail = get_processor().gmail
    if not gmail:
        try:
            from gmail_service import get_gmail_service
            gmail = get_gmail_service()
        except Exception:
            gmail = None

    if gmail:
        try:
            proc = EmailProcessor(gmail_service=gmail, storage=storage)
            sent = proc._send_reply(
                email_id,
                email["sender"],
                email["subject"],
                email["suggested_reply"],
            )
            if not sent:
                raise HTTPException(status_code=500, detail="Erreur envoi Gmail")
            storage.update_status(email_id, "sent", reviewer=current_user.email)
            from gmail_service import mark_email_as_read
            mark_email_as_read(gmail, email_id)
            return {"status": "sent", "email_id": email_id, "approved_by": current_user.email}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erreur envoi Gmail pour {email_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur envoi Gmail : {str(e)}")
    else:
        storage.update_status(email_id, "approved_no_gmail", reviewer=current_user.email)
        return {"status": "approved_no_gmail", "email_id": email_id, "approved_by": current_user.email}


@app.post("/emails/{email_id}/reject", tags=["Emails"])
def reject_email(
    email_id: str,
    current_user: User = Depends(get_current_user),
    reason: str = "",
):
    """Rejette la réponse générée — aucun email envoyé."""
    if current_user.role not in ("admin", "user"):
        raise HTTPException(status_code=403, detail="Accès refusé")

    storage = _get_storage()
    email = storage.get_by_id(email_id)

    if not email:
        raise HTTPException(status_code=404, detail="Email introuvable")
    if email.get("status") != "pending_review":
        raise HTTPException(status_code=400, detail=f"Statut invalide : {email.get('status')}")

    storage.update_status(
        email_id,
        "rejected",
        reviewer=current_user.email,
        rejection_reason=reason or None,
    )
    return {"status": "rejected", "email_id": email_id, "rejected_by": current_user.email}


@app.get("/emails/{email_id}", tags=["Emails"])
def get_email(email_id: str, current_user: User = Depends(get_current_user)):
    """Retourne le detail d un email traite par son ID."""
    record = _get_storage().get_by_id(email_id)
    if not record:
        raise HTTPException(404, f"Email '{email_id}' non trouve.")
    return record
