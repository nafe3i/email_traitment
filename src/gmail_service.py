"""
gmail_service.py — Client Gmail API pour AUI Email Support System.
Gère l'authentification OAuth2 avec chiffrement du token et la récupération des e-mails.
"""

import os
import json
import base64
import logging
import re
from email.utils import parseaddr
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

from config import settings
from secrets import SecretsManager

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_gmail_service() -> Resource:
    """
    Initialise et retourne le client API Gmail.
    Gère l'authentification OAuth2 et le déchiffrement du token de session.
    """
    creds = None
    token_path = Path(settings.GMAIL_TOKEN_PATH)
    creds_path = Path(settings.GMAIL_CREDENTIALS_PATH)
    
    manager = SecretsManager.from_env()

    # 1. Tenter de charger le token chiffré existant
    if token_path.exists():
        try:
            with open(token_path, "r", encoding="utf-8") as f:
                encrypted_token = f.read().strip()
            if encrypted_token:
                decrypted_token = manager.decrypt_token(encrypted_token)
                creds_info = json.loads(decrypted_token)
                creds = Credentials.from_authorized_user_info(creds_info, SCOPES)
                logger.info("Token OAuth2 déchiffré et chargé avec succès.")
        except Exception as e:
            logger.warning(f"Impossible de charger le token chiffré: {e}")
            creds = None

    # 2. Rafraîchir ou initier l'authentification si invalide
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Rafraîchissement du token OAuth2 expiré...")
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Échec du rafraîchissement du token: {e}")
                creds = None

        if not creds:
            if not creds_path.exists():
                raise FileNotFoundError(
                    f"Fichier de configuration client introuvable : '{creds_path}'. "
                    "Téléchargez credentials.json depuis Google Console et placez-le dans le dossier credentials/."
                )
            
            logger.info("Lancement du serveur d'authentification OAuth2 local...")
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        # 3. Chiffrer et sauvegarder le nouveau token
        try:
            token_json = creds.to_json()
            encrypted_token = manager.encrypt_token(token_json)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, "w", encoding="utf-8") as f:
                f.write(encrypted_token)
            logger.info("Nouveau token OAuth2 chiffré et sauvegardé.")
        except Exception as e:
            logger.error(f"Échec de l'enregistrement du token chiffré: {e}")

    return build("gmail", "v1", credentials=creds)


def _get_body_from_parts(parts_data: dict) -> str:
    """Parcourt récursivement les parts MIME pour extraire le texte brut."""
    if "parts" in parts_data:
        for part in parts_data["parts"]:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            elif mime_type == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    html_content = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                    # Nettoyer simplement le HTML en texte brut
                    text = re.sub(r"<[^<]+?>", "", html_content)
                    return text
            
            if "parts" in part:
                body = _get_body_from_parts(part)
                if body:
                    return body
    return ""


def parse_gmail_message(msg_data: dict) -> dict:
    """Transforme la réponse brute de l'API Gmail en dictionnaire standard."""
    headers = msg_data.get("payload", {}).get("headers", [])
    subject = ""
    sender = ""
    for h in headers:
        name = h.get("name", "").lower()
        if name == "subject":
            subject = h.get("value", "")
        elif name == "from":
            _, sender = parseaddr(h.get("value", ""))

    # Extraction du corps de l'e-mail
    payload = msg_data.get("payload", {})
    body = _get_body_from_parts(payload)
    if not body:
        body = payload.get("body", {}).get("data", "")
        if body:
            body = base64.urlsafe_b64decode(body).decode("utf-8", errors="ignore")

    return {
        "id": msg_data.get("id"),
        "sender": sender,
        "subject": subject,
        "body": body or "",
    }


def fetch_unread_emails(service: Resource, max_results: int = 20) -> List[dict]:
    """Récupère les e-mails non lus de la boîte de réception."""
    try:
        results = service.users().messages().list(
            userId="me", q="is:unread", maxResults=max_results
        ).execute()
        
        messages = results.get("messages", [])
        parsed_emails = []
        
        for msg in messages:
            msg_data = service.users().messages().get(
                userId="me", id=msg["id"], format="full"
            ).execute()
            
            email_info = parse_gmail_message(msg_data)
            parsed_emails.append(email_info)

        return parsed_emails
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des e-mails Gmail: {e}")
        return []


def mark_email_as_read(service: Resource, message_id: str) -> None:
    """Retire le label UNREAD après un traitement réussi."""
    try:
        service.users().messages().batchModify(
            userId="me",
            body={"ids": [message_id], "removeLabelIds": ["UNREAD"]},
        ).execute()
    except Exception as e:
        logger.error(f"Impossible de marquer l'email {message_id} comme lu: {e}")
