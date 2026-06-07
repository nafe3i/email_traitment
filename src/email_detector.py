"""
email_detector.py — Détecteur d'emails intelligent pour AUI Email Support System.

Détecte automatiquement :
  - La langue (français / anglais / arabe)
  - Le type d'expéditeur (étudiant AUI / parent / staff / externe)
  - Le niveau d'urgence (high / normal / low)
  - Le spam et les emails hors-sujet
  - Les doublons (emails déjà traités)
  - Le score de priorité global (0-100)

Aucune dépendance externe — stdlib + re uniquement.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set


# ─── Enums ────────────────────────────────────────────────────────────────────

class Language(str, Enum):
    FRENCH  = "fr"
    ENGLISH = "en"
    ARABIC  = "ar"
    UNKNOWN = "unknown"

class SenderType(str, Enum):
    STUDENT  = "student"
    PARENT   = "parent"
    STAFF    = "staff"
    EXTERNAL = "external"

class UrgencyLevel(str, Enum):
    HIGH   = "high"
    NORMAL = "normal"
    LOW    = "low"

class SpamReason(str, Enum):
    PROMOTIONAL = "promotional"
    OFF_TOPIC   = "off_topic"
    SUSPICIOUS  = "suspicious"
    NOT_SPAM    = "not_spam"


# ─── Résultat ─────────────────────────────────────────────────────────────────

@dataclass
class DetectionResult:
    language:       Language     = Language.UNKNOWN
    sender_type:    SenderType   = SenderType.EXTERNAL
    urgency:        UrgencyLevel = UrgencyLevel.NORMAL
    spam_reason:    SpamReason   = SpamReason.NOT_SPAM
    is_spam:        bool         = False
    is_duplicate:   bool         = False
    priority_score: int          = 50
    flags:          list         = field(default_factory=list)

    @property
    def should_process(self) -> bool:
        """True si l'email doit entrer dans le pipeline RAG."""
        return not self.is_spam and not self.is_duplicate

    def to_dict(self) -> dict:
        return {
            "language":       self.language.value,
            "sender_type":    self.sender_type.value,
            "urgency":        self.urgency.value,
            "spam_reason":    self.spam_reason.value,
            "is_spam":        self.is_spam,
            "is_duplicate":   self.is_duplicate,
            "priority_score": self.priority_score,
            "flags":          self.flags,
            "should_process": self.should_process,
        }


# ─── Détecteur ────────────────────────────────────────────────────────────────

class EmailDetector:
    """
    Analyse un email et retourne un DetectionResult.

    Usage :
        detector = EmailDetector(processed_ids=existing_set)
        result   = detector.detect(email_id, sender, subject, body)
        if result.should_process:
            # envoyer au pipeline RAG
    """

    # Patterns langue
    _FR_TOKENS = re.compile(
        r"\b(je|vous|nous|mon|ma|mes|votre|notre|est|sont|avec|pour|"
        r"bonjour|merci|cordialement|madame|monsieur|étudiant|université|"
        r"inscription|scolarité|cours|notes|emploi|bourse|frais|demande|"
        r"stage|bibliothèque|résidence|cantine)\b",
        re.IGNORECASE
    )
    _EN_TOKENS = re.compile(
        r"\b(I|you|we|my|your|our|is|are|with|for|"
        r"hello|dear|thank|sincerely|student|university|"
        r"enrollment|tuition|course|grade|schedule|scholarship|fee|request|"
        r"internship|library|dormitory|cafeteria)\b",
        re.IGNORECASE
    )
    _AR_PATTERN = re.compile(r"[\u0600-\u06FF]")

    # Patterns expéditeur
    _AUI_DOMAIN  = re.compile(r"@aui\.ma$", re.IGNORECASE)
    _STUDENT_ID  = re.compile(r"\b[a-z]{2,4}\d{5,6}\b", re.IGNORECASE)
    _PARENT_KW   = re.compile(
        r"\b(parent|father|mother|père|mère|guardian|tuteur|"
        r"mon fils|ma fille|my son|my daughter|fils|fille|enfant|child)\b",
        re.IGNORECASE
    )

    # Patterns urgence
    _URGENT_KW = re.compile(
        r"\b(urgent|urgently|immédiatement|immediately|asap|"
        r"as soon as possible|deadline|délai|date limite|dernier délai|"
        r"expiration|expire|tomorrow|demain|tonight|ce soir|"
        r"aujourd'hui|today|last chance|dernière chance|critical|critique)\b",
        re.IGNORECASE
    )
    _LOW_KW = re.compile(
        r"\b(just wondering|curious|whenever|quand vous pouvez|"
        r"no rush|pas pressé|en passant|par curiosité|renseignement général|"
        r"juste pour savoir|simple question)\b",
        re.IGNORECASE
    )

    # Patterns spam
    _PROMO_KW = re.compile(
        r"\b(promo|discount|offer|offre|solde|deal|win|gagner|prize|"
        r"click here|cliquez ici|unsubscribe|désabonner|"
        r"congratulations|félicitations|you.ve been selected|"
        r"free|gratuit|limited time|temps limité)\b",
        re.IGNORECASE
    )
    _OFF_TOPIC_KW = re.compile(
        r"\b(crypto|bitcoin|nft|investment|invest|forex|trading|"
        r"casino|bet|loan|prêt|crédit rapide|mortgage|"
        r"weight loss|perte de poids|diet pill|"
        r"viagra|pharmacy|pharmacie en ligne|adult|escort)\b",
        re.IGNORECASE
    )
    _SUSPICIOUS = [
        re.compile(r"http[s]?://(?!aui\.ma)", re.IGNORECASE),
        re.compile(r"\$\$\$|€€€|argent facile", re.IGNORECASE),
        re.compile(r"[A-Z]{6,}"),
    ]

    def __init__(self, processed_ids: Optional[Set[str]] = None):
        self._processed_ids: Set[str] = processed_ids or set()

    # ── API publique ──────────────────────────────────────────────────────────

    def detect(self, email_id: str, sender: str, subject: str, body: str) -> DetectionResult:
        full_text = f"{subject} {body}"
        r = DetectionResult()

        r.language       = self._detect_language(full_text)
        r.sender_type    = self._detect_sender(sender, full_text)
        r.urgency        = self._detect_urgency(full_text)
        r.is_duplicate   = email_id in self._processed_ids
        spam             = self._detect_spam(subject, body)
        r.spam_reason    = spam
        r.is_spam        = spam != SpamReason.NOT_SPAM
        r.priority_score = self._compute_priority(r)
        r.flags          = self._build_flags(r)
        return r

    def mark_processed(self, email_id: str) -> None:
        self._processed_ids.add(email_id)

    def get_processed_count(self) -> int:
        return len(self._processed_ids)

    # ── Détections internes ───────────────────────────────────────────────────

    def _detect_language(self, text: str) -> Language:
        if len(self._AR_PATTERN.findall(text)) > 5:
            return Language.ARABIC
        fr = len(self._FR_TOKENS.findall(text))
        en = len(self._EN_TOKENS.findall(text))
        if fr == 0 and en == 0:
            return Language.UNKNOWN
        return Language.FRENCH if fr >= en else Language.ENGLISH

    def _detect_sender(self, sender: str, full_text: str) -> SenderType:
        if not sender:
            return SenderType.EXTERNAL
        if self._PARENT_KW.search(full_text):
            return SenderType.PARENT
        if self._AUI_DOMAIN.search(sender):
            local = sender.split("@")[0]
            return SenderType.STUDENT if self._STUDENT_ID.match(local) else SenderType.STAFF
        if self._STUDENT_ID.search(full_text):
            return SenderType.STUDENT
        return SenderType.EXTERNAL

    def _detect_urgency(self, text: str) -> UrgencyLevel:
        if self._URGENT_KW.search(text):
            return UrgencyLevel.HIGH
        if self._LOW_KW.search(text):
            return UrgencyLevel.LOW
        return UrgencyLevel.NORMAL

    def _detect_spam(self, subject: str, body: str) -> SpamReason:
        full = f"{subject} {body}"
        if self._PROMO_KW.search(full):
            return SpamReason.PROMOTIONAL
        if self._OFF_TOPIC_KW.search(full):
            return SpamReason.OFF_TOPIC
        hits = sum(1 for p in self._SUSPICIOUS if p.search(full))
        if hits >= 2:
            return SpamReason.SUSPICIOUS
        return SpamReason.NOT_SPAM

    def _compute_priority(self, r: DetectionResult) -> int:
        score = 50
        if r.urgency == UrgencyLevel.HIGH:
            score += 30
        elif r.urgency == UrgencyLevel.LOW:
            score -= 20
        if r.sender_type == SenderType.STUDENT:
            score += 10
        elif r.sender_type == SenderType.PARENT:
            score += 5
        elif r.sender_type == SenderType.EXTERNAL:
            score -= 10
        if r.is_spam:
            score = 0
        return max(0, min(100, score))

    def _build_flags(self, r: DetectionResult) -> list:
        flags = []
        if r.is_duplicate:           flags.append("duplicate")
        if r.is_spam:                flags.append(f"spam:{r.spam_reason.value}")
        if r.urgency == UrgencyLevel.HIGH:   flags.append("urgent")
        if r.language == Language.UNKNOWN:   flags.append("unknown_language")
        if r.sender_type == SenderType.EXTERNAL: flags.append("external_sender")
        return flags
