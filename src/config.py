"""
config.py — Configuration Management with Pydantic

✅ ÉTAPE 4 DE PHASE 1: CONFIGURATION MANAGEMENT

Fonctionnalités:
  - Environment variables management
  - Type validation
  - Default values
  - Required variables checking
  - Single source of truth

Utilisation:
    from config import settings
    
    print(settings.OLLAMA_BASE)
    print(settings.JWT_SECRET)
"""

import os
from pathlib import Path
from typing import Optional, List, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


# ─── Configuration Class ──────────────────────────────────────────────────────

class Settings(BaseSettings):
    """
    Configuration pour l'application AUI Email Support System.
    
    Variables d'environnement:
        - SERVER_*: Configuration serveur
        - OLLAMA_*: Configuration Ollama
        - RAG_*: Configuration RAG
        - DB_*: Configuration base de données
        - SECURITY_*: Configuration sécurité
        - JWT_*: Configuration JWT
    """
    
    # ─── SERVER SETTINGS ───────────────────────────────────────────────────────
    
    DEBUG: bool = Field(default=False, description="Mode debug")
    HOST: str = Field(default="0.0.0.0", description="Adresse serveur")
    PORT: int = Field(default=8000, description="Port serveur", ge=1024, le=65535)
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    
    # ─── OLLAMA SETTINGS ───────────────────────────────────────────────────────
    
    OLLAMA_BASE: str = Field(
        default="http://localhost:11434",
        description="Ollama base URL"
    )
    OLLAMA_TIMEOUT: int = Field(default=60, ge=10, le=300, description="Ollama timeout in seconds")
    OLLAMA_EMBED_MODEL: str = Field(default="nomic-embed-text", description="Embedding model")
    OLLAMA_LLM_MODEL: str = Field(default="mistral", description="LLM model")
    
    # ─── RAG SETTINGS ──────────────────────────────────────────────────────────
    
    TOP_K: int = Field(default=3, ge=1, le=10, description="Number of RAG results")
    CONFIDENCE_THRESHOLD: float = Field(default=0.50, ge=0.0, le=1.0, description="Min confidence")
    
    # ─── DATABASE SETTINGS ────────────────────────────────────────────────────
    
    CHROMA_PATH: str = Field(
        default="./data/chroma_db",
        description="Path to ChromaDB"
    )
    REPORT_PATH: str = Field(
        default="./data/reports/report.json",
        description="Path to report file"
    )
    BACKUP_PATH: str = Field(
        default="./data/backups",
        description="Path to backups"
    )
    
    # ─── SECURITY SETTINGS ────────────────────────────────────────────────────
    
    SECRET_KEY: str = Field(
        ...,  # Required!
        description="Master encryption key for Fernet"
    )
    JWT_SECRET: str = Field(
        ...,  # Required!
        description="Secret key for JWT signing"
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRY_HOURS: int = Field(default=24, ge=1, le=720, description="JWT expiry in hours")
    
    # ─── CORS SETTINGS ────────────────────────────────────────────────────────
    
    ALLOWED_ORIGINS: Any = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:5173",
        ],
        description="CORS allowed origins"
    )
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v
    
    # ─── RATE LIMITING ────────────────────────────────────────────────────────
    
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_PER_PROCESS: str = Field(default="10/minute", description="Per-endpoint rate limit")
    RATE_LIMIT_STORAGE: str = Field(default="memory://", description="Rate limit storage backend")
    
    # ─── LOGGING SETTINGS ────────────────────────────────────────────────────
    
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Log format: json or text")
    
    # ─── EMAIL SETTINGS (pour Gmail) ───────────────────────────────────────────
    
    GMAIL_CREDENTIALS_PATH: str = Field(
        default="./credentials/credentials.json",
        description="Path to Gmail credentials"
    )
    GMAIL_TOKEN_PATH: str = Field(
        default="./credentials/token.json",
        description="Path to Gmail token"
    )
    
    # ─── Pydantic Configuration ────────────────────────────────────────────────
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignorer variables non définies
    
    # ─── Validation Methods ───────────────────────────────────────────────────
    
    def validate_paths(self):
        """Valide que les chemins sont valides."""
        paths = [
            ("CHROMA_PATH", self.CHROMA_PATH),
            ("BACKUP_PATH", self.BACKUP_PATH),
        ]
        
        for name, path in paths:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            print(f"✅ {name}: {path}")
    
    def validate_security(self):
        """Valide les paramètres de sécurité."""
        errors = []
        
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 20:
            errors.append("SECRET_KEY too short (min 20 chars)")
        
        if not self.JWT_SECRET or len(self.JWT_SECRET) < 20:
            errors.append("JWT_SECRET too short (min 20 chars)")
        
        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                errors.append("Debug must be False in production")
            if "localhost" in self.OLLAMA_BASE:
                errors.append("Cannot use localhost for Ollama in production")
        
        if errors:
            raise ValueError(f"Security validation failed: {'; '.join(errors)}")
        
        print("✅ Security validation: PASS")
    
    def log_startup(self):
        """Log la configuration au démarrage."""
        print(f"🚀 Starting in {self.ENVIRONMENT} mode")
        print(f"  Server: {self.HOST}:{self.PORT}")
        print(f"  Ollama: {self.OLLAMA_BASE}")
        print(f"  ChromaDB: {self.CHROMA_PATH}")
        print(f"  CORS Origins: {len(self.ALLOWED_ORIGINS)} allowed")


# ─── Create Settings Instance ────────────────────────────────────────────────

def load_settings() -> Settings:
    """
    Charge les settings depuis .env ou variables d'environnement.
    
    Returns:
        Settings instance
        
    Raises:
        ValueError: Si variables requises manquent
    """
    try:
        settings = Settings()
    except Exception as e:
        print(f"❌ Configuration Error: {e}")
        print("\nRequired environment variables:")
        print("  - SECRET_KEY (generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')")
        print("  - JWT_SECRET (any long random string)")
        raise
    
    # Validations
    settings.validate_security()
    settings.validate_paths()
    settings.log_startup()
    
    return settings


# ─── Global Settings Instance ────────────────────────────────────────────────

try:
    settings = load_settings()
except Exception as e:
    # En développement, créer un dummy pour permettre imports
    if os.getenv("ENVIRONMENT") != "production":
        print(f"⚠️  Using fallback settings: {e}")
        settings = None  # À gérer dans l'app startup
    else:
        raise


# ─── Development Helper ───────────────────────────────────────────────────────

def print_env_template():
    """Affiche un template .env avec toutes les variables."""
    print("""
# .env.example - Copy and fill with your values

# Server
DEBUG=false
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development

# Ollama
OLLAMA_BASE=http://localhost:11434
OLLAMA_TIMEOUT=60
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_LLM_MODEL=mistral

# RAG
TOP_K=3
CONFIDENCE_THRESHOLD=0.50

# Database
CHROMA_PATH=./data/chroma_db
REPORT_PATH=./data/reports/report.json
BACKUP_PATH=./data/backups

# Security (REQUIRED!)
SECRET_KEY=your-fernet-key-here
JWT_SECRET=your-jwt-secret-here
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080,https://aui.ma

# Rate Limiting
RATE_LIMIT_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Gmail (if using email features)
GMAIL_CREDENTIALS_PATH=./credentials/credentials.json
GMAIL_TOKEN_PATH=./credentials/token.json
    """)


if __name__ == "__main__":
    print_env_template()
