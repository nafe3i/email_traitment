"""
sanitizer.py — Nettoyage complet des emails reels pour AUI Email Support System.

Gere :
  - Signatures (fr/en/ar)
  - Citations et historique de conversation (>, On ... wrote:, -----Original Message-----)
  - Forwarded messages
  - Separateurs Outlook/Gmail
  - Numeros de telephone, fax
  - Disclaimers legaux
  - Lignes vides excessives
  - Caracteres de controle
  - Detection injection prompt LLM
"""

import re
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)

# ─── Patterns nettoyage email ──────────────────────────────────────────────────

# Signatures francaises / anglaises / arabes
_SIGNATURES = [
    re.compile(r"cordialement[\s,\.]*\n.*",           re.DOTALL | re.IGNORECASE),
    re.compile(r"bien cordialement[\s,\.]*\n.*",       re.DOTALL | re.IGNORECASE),
    re.compile(r"salutations[\s,\.]*\n.*",             re.DOTALL | re.IGNORECASE),
    re.compile(r"best regards[\s,\.]*\n.*",            re.DOTALL | re.IGNORECASE),
    re.compile(r"kind regards[\s,\.]*\n.*",            re.DOTALL | re.IGNORECASE),
    re.compile(r"sincerely[\s,\.]*\n.*",               re.DOTALL | re.IGNORECASE),
    re.compile(r"regards[\s,\.]*\n.*",                 re.DOTALL | re.IGNORECASE),
    re.compile(r"thank you[\s,\.]*\n.*",               re.DOTALL | re.IGNORECASE),
    re.compile(r"merci[\s,\.]*\n.*",                   re.DOTALL | re.IGNORECASE),
    re.compile(r"avec mes salutations.*",              re.DOTALL | re.IGNORECASE),
    re.compile(r"شكرا.*",                              re.DOTALL),
    re.compile(r"مع التحية.*",                         re.DOTALL),
]

# Separateurs de citation / historique
_QUOTE_SEPARATORS = [
    re.compile(r"-{3,}.*?(original message|message original|begin forwarded|forwarded message).*?-{3,}.*", re.DOTALL | re.IGNORECASE),
    re.compile(r"_{3,}\n.*",                           re.DOTALL),
    re.compile(r"on\s.{5,80}\s(wrote|a écrit)\s*:.*", re.DOTALL | re.IGNORECASE),
    re.compile(r"le\s.{5,80}\sa écrit\s*:.*",         re.DOTALL | re.IGNORECASE),
    re.compile(r"de\s*:.*\nobjet\s*:.*",               re.DOTALL | re.IGNORECASE),
    re.compile(r"from\s*:.*\nsubject\s*:.*",           re.DOTALL | re.IGNORECASE),
    re.compile(r"^>+.*$",                              re.MULTILINE),
    re.compile(r"\[cid:.*?\]",                         re.IGNORECASE),
]

# Blocs disclaimer legaux
_DISCLAIMERS = [
    re.compile(r"(this (email|message|communication) (is|contains|may).{0,300}(confidential|privileged)).*", re.DOTALL | re.IGNORECASE),
    re.compile(r"(ce (message|courriel|email) (est|contient).{0,300}(confidentiel|privilégié)).*",           re.DOTALL | re.IGNORECASE),
    re.compile(r"(avertissement|disclaimer|notice légale)\s*:.*",                                            re.DOTALL | re.IGNORECASE),
]

# Informations de contact dans la signature
_CONTACT_INFO = [
    re.compile(r"\b(tél|tel|phone|fax|mobile|gsm|portable)\s*[:\.]?\s*[\+\d\s\-\(\)]{7,20}", re.IGNORECASE),
    re.compile(r"\b\d{2}[\s\-\.]\d{2}[\s\-\.]\d{2}[\s\-\.]\d{2}[\s\-\.]\d{2}\b"),  # 06-XX-XX-XX-XX
    re.compile(r"\+212[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{3}"),                        # +212 format Maroc
]

# Autres nettoyages
_URLS        = re.compile(r"http[s]?://\S+")
_EMAILS_SIG  = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_WHITESPACE  = re.compile(r"\n{3,}")
_CTRL_CHARS  = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


# ─── Patterns injection prompt LLM ────────────────────────────────────────────

_INJECTION_PATTERNS = {
    "system_override":  re.compile(r"\b(ignore|forget|override|bypass|disregard)\b.{0,50}(instruction|prompt|system)", re.IGNORECASE),
    "jailbreak":        re.compile(r"\b(pretend|roleplay|act as|you are now|imagine you)\b", re.IGNORECASE),
    "code_execution":   re.compile(r"(import os|exec\(|eval\(|__import__|subprocess)", re.IGNORECASE),
    "prompt_injection": re.compile(r"\n\s*(system|prompt|instruction)\s*:", re.IGNORECASE),
}


# ─── Fonction principale ───────────────────────────────────────────────────────

def clean_email_body(text: str) -> str:
    """
    Nettoie le corps d un email reel.

    Supprime dans cet ordre :
    1. Caracteres de controle
    2. Blocs disclaimer legaux
    3. Separateurs de citation et historique conversation
    4. Signatures
    5. Informations de contact
    6. URLs
    7. Lignes vides excessives

    Returns:
        Texte nettoy et pret pour le pipeline RAG
    """
    if not text or not isinstance(text, str):
        return ""

    # 1. Caracteres de controle
    text = _CTRL_CHARS.sub("", text)

    # 2. Disclaimers legaux
    for pat in _DISCLAIMERS:
        text = pat.sub("", text)

    # 3. Citations et historique
    for pat in _QUOTE_SEPARATORS:
        text = pat.sub("", text)

    # 4. Signatures
    for pat in _SIGNATURES:
        text = pat.sub("", text)

    # 5. Informations de contact (telephone, etc.)
    for pat in _CONTACT_INFO:
        text = pat.sub("", text)

    # 6. URLs
    text = _URLS.sub("", text)

    # 7. Emails dans signature (garder seulement le contenu utile)
    # On ne supprime pas les emails mentionnes dans le corps (ex: "contactez helpdesk@aui.ma")
    # mais on supprime les lignes qui ne contiennent QUE un email (typique des signatures)
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and re.fullmatch(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", stripped):
            continue  # ligne = juste un email → signature
        lines.append(line)
    text = "\n".join(lines)

    # 8. Lignes vides excessives
    text = _WHITESPACE.sub("\n\n", text)

    return text.strip()


def clean_subject(subject: str) -> str:
    """
    Nettoie le sujet d un email.
    Supprime les prefixes Re:/Fwd:/TR:/Rép: en cascade.
    """
    if not subject:
        return ""
    cleaned = re.sub(r"^(re|fwd|fw|tr|rép|réf|ref)\s*:\s*", "", subject.strip(), flags=re.IGNORECASE)
    # Appliquer plusieurs fois pour les cascades (Re: Re: Re:)
    while True:
        new = re.sub(r"^(re|fwd|fw|tr|rép|réf|ref)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
        if new == cleaned:
            break
        cleaned = new
    return cleaned.strip()


def detect_injection(text: str) -> List[str]:
    """Detecte les tentatives d injection de prompt LLM. Retourne la liste des patterns trouves."""
    found = []
    for name, pat in _INJECTION_PATTERNS.items():
        if pat.search(text):
            found.append(name)
            logger.warning(f"Injection pattern detected: {name} | preview: {text[:80]}")
    return found


def sanitize_email(sender: str, subject: str, body: str) -> Tuple[str, str, str]:
    """
    Point d entree unique — nettoie les 3 champs d un email.

    Returns:
        (sender, subject_clean, body_clean)
    """
    subject_clean = clean_subject(subject)
    body_clean    = clean_email_body(body)

    # Detection injection (log seulement, ne bloque pas)
    detect_injection(f"{subject_clean} {body_clean}")

    # Truncature de securite
    body_clean = body_clean[:5000]

    sender_clean = sender.strip().lower() if isinstance(sender, str) else ""
    return sender_clean, subject_clean, body_clean
