═══════════════════════════════════════════════════════════════════════════════
📚 PHASE 2 — POSTGRESQL DATABASE SCHEMA
═══════════════════════════════════════════════════════════════════════════════

Project: AUI Email Support System
Phase: 2 — Database & Persistence
Focus: User Management, Email Logs, RAG Storage
Status: 📋 DESIGN DOCUMENT

═══════════════════════════════════════════════════════════════════════════════
🔄 CURRENT STATE vs PHASE 2
═══════════════════════════════════════════════════════════════════════════════

PHASE 1 (Actuellement):
  ❌ Users: Dictionnaire Python en mémoire
  ❌ Logs: Console logs seulement
  ❌ Persistence: Aucune
  ❌ Scalability: Pas de réplication

PHASE 2 (À Implémenter):
  ✅ Users: PostgreSQL Table
  ✅ Logs: Database logs + journalisation
  ✅ Persistence: Sauvegarde sur disque
  ✅ Scalability: Connection pooling + migrations

═══════════════════════════════════════════════════════════════════════════════
📊 DATABASE SCHEMA COMPLET
═══════════════════════════════════════════════════════════════════════════════

1️⃣ TABLE: users (Utilisateurs)
────────────────────────────────────────────────────────────────────────────────

Purpose: Enregistrer les utilisateurs du système

SQL Definition:
┌──────────────────────────────────────────────────────────────────────────────┐
│ CREATE TABLE users (                                                         │
│     -- Clés primaires & identifiants                                         │
│     id SERIAL PRIMARY KEY,                                                   │
│     uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),                    │
│                                                                              │
│     -- Identification                                                        │
│     email VARCHAR(254) UNIQUE NOT NULL,                                     │
│     username VARCHAR(100) UNIQUE,                                           │
│     first_name VARCHAR(100),                                                │
│     last_name VARCHAR(100),                                                 │
│                                                                              │
│     -- Authentification                                                      │
│     hashed_password VARCHAR(255) NOT NULL,                                  │
│     password_changed_at TIMESTAMP,                                          │
│                                                                              │
│     -- Rôles & Permissions                                                  │
│     role VARCHAR(50) NOT NULL DEFAULT 'user',                              │
│       CHECK (role IN ('admin', 'user', 'viewer')),                         │
│                                                                              │
│     -- État du compte                                                        │
│     is_active BOOLEAN DEFAULT true,                                         │
│     is_verified BOOLEAN DEFAULT false,                                      │
│     email_verified_at TIMESTAMP,                                            │
│     last_login_at TIMESTAMP,                                                │
│                                                                              │
│     -- 2FA (Two-Factor Authentication)                                      │
│     two_factor_enabled BOOLEAN DEFAULT false,                               │
│     two_factor_secret VARCHAR(255),                                         │
│                                                                              │
│     -- Métadonnées                                                           │
│     metadata JSONB DEFAULT '{}',                                            │
│     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                         │
│     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                         │
│     deleted_at TIMESTAMP                                                    │
│ );                                                                           │
│                                                                              │
│ -- Indexes                                                                  │
│ CREATE INDEX idx_users_email ON users(email);                              │
│ CREATE INDEX idx_users_role ON users(role);                                │
│ CREATE INDEX idx_users_is_active ON users(is_active);                      │
│ CREATE INDEX idx_users_created_at ON users(created_at);                    │
└──────────────────────────────────────────────────────────────────────────────┘

Fields Explanation:

  id (SERIAL PRIMARY KEY)
    - Clé primaire auto-incrémentale
    - Usage: Référence interne
    
  uuid (UUID UNIQUE)
    - Identifiant universel unique
    - Usage: APIs, URLs publiques (jamais le SERIAL id)
    
  email (VARCHAR 254)
    - Email unique (RFC 5321 limit 254 chars)
    - Validation: EmailStr de Pydantic
    - Index: Oui (queries fréquentes)
    
  hashed_password (VARCHAR 255)
    - Hash bcrypt du mot de passe
    - Jamais stocker plaintext!
    - Généré avec passlib (Phase 1)
    
  role (VARCHAR 50)
    - 'admin': Accès total
    - 'user': Utilisateur normal (par défaut)
    - 'viewer': Accès lecture-seule
    - Constraint: CHECK pour valeurs autorisées
    
  is_active (BOOLEAN)
    - Permet soft-delete (pas de suppression réelle)
    - Utilisé dans les queries (WHERE is_active = true)
    
  is_verified (BOOLEAN)
    - Email vérifié oui/non
    - Phase 3: Ajouter vérification par email
    
  two_factor_enabled (BOOLEAN)
    - 2FA activé oui/non
    - Phase 4: Implémenter TOTP
    
  metadata (JSONB)
    - Données flexibles (profile picture URL, etc)
    - JSONB: Queryable, indexable
    
  created_at / updated_at (TIMESTAMP)
    - Audit trail
    - Utile pour logs & rapports

2️⃣ TABLE: email_logs (Historique des Emails)
────────────────────────────────────────────────────────────────────────────────

Purpose: Tracer tous les emails traités

SQL Definition:
┌──────────────────────────────────────────────────────────────────────────────┐
│ CREATE TABLE email_logs (                                                    │
│     -- Clés                                                                  │
│     id SERIAL PRIMARY KEY,                                                   │
│     uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),                    │
│                                                                              │
│     -- Référence utilisateur                                                │
│     user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,        │
│                                                                              │
│     -- Contenu email                                                         │
│     sender VARCHAR(254) NOT NULL,                                           │
│     subject VARCHAR(500) NOT NULL,                                          │
│     body TEXT NOT NULL,                                                     │
│     body_hash VARCHAR(64),          -- SHA256 du body (déduplicate)        │
│                                                                              │
│     -- Traitement                                                            │
│     status VARCHAR(50) DEFAULT 'pending',                                   │
│       CHECK (status IN ('pending', 'processing', 'success', 'failed')),    │
│     response TEXT,                                                          │
│     response_time_ms INTEGER,                                               │
│     error_message TEXT,                                                     │
│                                                                              │
│     -- Modèle LLM utilisé                                                   │
│     model_used VARCHAR(100),                                                │
│     tokens_used INTEGER,                                                    │
│     cost_cents INTEGER,             -- Coût en centimes (pour billing)     │
│                                                                              │
│     -- Métadonnées                                                           │
│     metadata JSONB DEFAULT '{}',                                            │
│     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                         │
│     processed_at TIMESTAMP,                                                 │
│     CONSTRAINT check_timestamp CHECK (processed_at >= created_at)          │
│ );                                                                           │
│                                                                              │
│ -- Indexes                                                                  │
│ CREATE INDEX idx_email_logs_user_id ON email_logs(user_id);                │
│ CREATE INDEX idx_email_logs_status ON email_logs(status);                  │
│ CREATE INDEX idx_email_logs_created_at ON email_logs(created_at);          │
│ CREATE INDEX idx_email_logs_body_hash ON email_logs(body_hash);            │
└──────────────────────────────────────────────────────────────────────────────┘

Fields Explanation:

  user_id (INTEGER REFERENCES users)
    - Clé étrangère vers users
    - ON DELETE CASCADE: Supprimer logs si user supprimé
    - Index: Oui (queries par user)
    
  status (VARCHAR 50)
    - 'pending': En attente de traitement
    - 'processing': En cours de traitement
    - 'success': Réponse générée
    - 'failed': Erreur dans le traitement
    
  response_time_ms (INTEGER)
    - Temps de réponse en millisecondes
    - Utile pour monitoring & performance
    
  body_hash (VARCHAR 64)
    - SHA256 hash du body
    - Détecte les emails dupliqués
    - Utile pour éviter le traitement dupliqué
    
  cost_cents (INTEGER)
    - Coût en centimes
    - Phase 3: Billing & usage tracking
    
  metadata (JSONB)
    - RAG context used, confidence score, etc

3️⃣ TABLE: rag_documents (Documents RAG / Base de Connaissances)
────────────────────────────────────────────────────────────────────────────────

Purpose: Enregistrer les documents utilisés pour le RAG

SQL Definition:
┌──────────────────────────────────────────────────────────────────────────────┐
│ CREATE TABLE rag_documents (                                                 │
│     -- Clés                                                                  │
│     id SERIAL PRIMARY KEY,                                                   │
│     uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),                    │
│     chroma_id VARCHAR(255) UNIQUE NOT NULL,  -- ID dans ChromaDB           │
│                                                                              │
│     -- Référence utilisateur (optionnel - pour isolation données)          │
│     user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,                │
│                                                                              │
│     -- Contenu                                                               │
│     title VARCHAR(500) NOT NULL,                                            │
│     content TEXT NOT NULL,                                                  │
│     content_hash VARCHAR(64) UNIQUE,                                        │
│     source_url VARCHAR(2000),                                               │
│                                                                              │
│     -- Catégorisation                                                        │
│     category VARCHAR(100),                                                  │
│     tags TEXT[],                 -- Array de tags                          │
│     language VARCHAR(10) DEFAULT 'en',                                      │
│                                                                              │
│     -- Métadonnées RAG                                                      │
│     embedding_model VARCHAR(100),                                           │
│     embedding_dimension INTEGER,                                            │
│     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,                         │
│     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP                          │
│ );                                                                           │
│                                                                              │
│ -- Indexes                                                                  │
│ CREATE INDEX idx_rag_documents_user_id ON rag_documents(user_id);          │
│ CREATE INDEX idx_rag_documents_chroma_id ON rag_documents(chroma_id);      │
│ CREATE INDEX idx_rag_documents_category ON rag_documents(category);        │
└──────────────────────────────────────────────────────────────────────────────┘

4️⃣ TABLE: api_tokens (Authentification API)
────────────────────────────────────────────────────────────────────────────────

Purpose: Gérer les tokens API pour accès programmatique

SQL Definition:
┌──────────────────────────────────────────────────────────────────────────────┐
│ CREATE TABLE api_tokens (                                                    │
│     -- Clés                                                                  │
│     id SERIAL PRIMARY KEY,                                                   │
│     uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),                    │
│                                                                              │
│     -- Référence utilisateur                                                │
│     user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,        │
│                                                                              │
│     -- Token                                                                 │
│     token_hash VARCHAR(255) UNIQUE NOT NULL,  -- Hash du token             │
│     token_prefix VARCHAR(20),                  -- Prefix du token (visible) │
│                                                                              │
│     -- Permissions                                                           │
│     scopes TEXT[],                 -- 'read', 'write', 'admin'              │
│     expires_at TIMESTAMP,                                                   │
│     last_used_at TIMESTAMP,                                                 │
│                                                                              │
│     -- État                                                                  │
│     is_active BOOLEAN DEFAULT true,                                         │
│     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP                          │
│ );                                                                           │
│                                                                              │
│ -- Indexes                                                                  │
│ CREATE INDEX idx_api_tokens_user_id ON api_tokens(user_id);                │
│ CREATE INDEX idx_api_tokens_token_hash ON api_tokens(token_hash);          │
│ CREATE INDEX idx_api_tokens_is_active ON api_tokens(is_active);            │
└──────────────────────────────────────────────────────────────────────────────┘

5️⃣ TABLE: audit_logs (Logs d'Audit Sécurité)
────────────────────────────────────────────────────────────────────────────────

Purpose: Enregistrer toutes les actions sensibles

SQL Definition:
┌──────────────────────────────────────────────────────────────────────────────┐
│ CREATE TABLE audit_logs (                                                    │
│     -- Clés                                                                  │
│     id BIGSERIAL PRIMARY KEY,       -- BigSerial car beaucoup de logs     │
│     uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),                    │
│                                                                              │
│     -- Référence utilisateur                                                │
│     user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,               │
│     ip_address INET,                                                        │
│     user_agent TEXT,                                                        │
│                                                                              │
│     -- Action                                                                │
│     action VARCHAR(100) NOT NULL,   -- 'login', 'password_change', etc    │
│     resource VARCHAR(100),           -- 'user', 'email_log', etc           │
│     resource_id INTEGER,                                                    │
│                                                                              │
│     -- Résultat                                                              │
│     status VARCHAR(20),              -- 'success', 'failure'                │
│     details JSONB DEFAULT '{}',                                             │
│     error_message TEXT,                                                     │
│                                                                              │
│     -- Timestamps                                                            │
│     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP                          │
│ );                                                                           │
│                                                                              │
│ -- Indexes (très importants pour audit logs)                              │
│ CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);                │
│ CREATE INDEX idx_audit_logs_action ON audit_logs(action);                  │
│ CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);          │
│ CREATE INDEX idx_audit_logs_ip_address ON audit_logs(ip_address);          │
└──────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
🔗 RELATIONSHIPS DIAGRAM
═══════════════════════════════════════════════════════════════════════════════

users (1)
  ├─── (Many) email_logs
  ├─── (Many) rag_documents
  ├─── (Many) api_tokens
  └─── (Many) audit_logs


Relationships:
  users.id ←→ email_logs.user_id
  users.id ←→ rag_documents.user_id
  users.id ←→ api_tokens.user_id
  users.id ←→ audit_logs.user_id

═══════════════════════════════════════════════════════════════════════════════
🐍 SQLALCHEMY ORM MODELS
═══════════════════════════════════════════════════════════════════════════════

À implémenter en Phase 2:

File: src/models/user.py
────────────────────────────────────────────────────────────────────────────────

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSONB, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"
    
    # Clés
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    
    # Identification
    email = Column(String(254), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    # Authentification
    hashed_password = Column(String(255), nullable=False)
    password_changed_at = Column(DateTime)
    
    # Rôles
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False, index=True)
    
    # État
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime)
    last_login_at = Column(DateTime)
    
    # 2FA
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))
    
    # Métadonnées
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    
    # Relationships
    email_logs = relationship("EmailLog", back_populates="user")
    rag_documents = relationship("RAGDocument", back_populates="user")
    api_tokens = relationship("APIToken", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.email}>"
```

File: src/models/email_log.py
────────────────────────────────────────────────────────────────────────────────

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

class EmailStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"

class EmailLog(Base):
    __tablename__ = "email_logs"
    
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    
    # Clé étrangère
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    user = relationship("User", back_populates="email_logs")
    
    # Contenu
    sender = Column(String(254), nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    body_hash = Column(String(64), index=True)
    
    # Traitement
    status = Column(Enum(EmailStatus), default=EmailStatus.PENDING, index=True)
    response = Column(Text)
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    
    # Modèle LLM
    model_used = Column(String(100))
    tokens_used = Column(Integer)
    cost_cents = Column(Integer)
    
    # Métadonnées
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime)
```

═══════════════════════════════════════════════════════════════════════════════
🚀 MIGRATION STRATEGY (Alembic)
═══════════════════════════════════════════════════════════════════════════════

Phase 2 Task: Set up Alembic for database migrations

Structure:
```
alembic/
├── versions/
│   ├── 001_create_users_table.py
│   ├── 002_create_email_logs_table.py
│   ├── 003_create_rag_documents_table.py
│   ├── 004_create_api_tokens_table.py
│   └── 005_create_audit_logs_table.py
├── env.py
├── script.py.mako
└── alembic.ini
```

Example Migration:
┌──────────────────────────────────────────────────────────────────────────────┐
│ # alembic/versions/001_create_users_table.py                                │
│                                                                              │
│ from alembic import op                                                      │
│ import sqlalchemy as sa                                                     │
│ from sqlalchemy.dialects import postgresql                                  │
│                                                                              │
│ def upgrade():                                                              │
│     op.create_table(                                                        │
│         'users',                                                            │
│         sa.Column('id', sa.Integer(), nullable=False),                     │
│         sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),  │
│         sa.Column('email', sa.String(254), nullable=False),                │
│         sa.Column('hashed_password', sa.String(255), nullable=False),      │
│         sa.Column('role', sa.String(50), nullable=False),                  │
│         sa.Column('is_active', sa.Boolean(), default=True),                │
│         sa.Column('created_at', sa.DateTime(), default=sa.func.now()),     │
│         sa.PrimaryKeyConstraint('id'),                                     │
│         sa.UniqueConstraint('email')                                       │
│     )                                                                       │
│     op.create_index('idx_users_email', 'users', ['email'])                 │
│                                                                              │
│ def downgrade():                                                            │
│     op.drop_index('idx_users_email')                                       │
│     op.drop_table('users')                                                 │
└──────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
🔐 SECURITY CONSIDERATIONS
═══════════════════════════════════════════════════════════════════════════════

1. PASSWORD HASHING
   ✅ Never store plaintext passwords
   ✅ Use bcrypt (already in Phase 1)
   ✅ Cost factor: 12 (Phase 1 default)
   
   Example:
   ```python
   from passlib.context import CryptContext
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
   hashed = pwd_context.hash("password")
   ```

2. ENCRYPTION FOR SENSITIVE DATA
   ✅ Encrypt api_tokens before storage
   ✅ Encrypt two_factor_secret
   
   Example:
   ```python
   from src.secrets import SecretsManager
   manager = SecretsManager.from_env()
   encrypted_token = manager.encrypt_token(token)
   ```

3. SOFT DELETES
   ✅ Use deleted_at TIMESTAMP instead of DELETE
   ✅ Soft delete: UPDATE users SET deleted_at = NOW()
   ✅ Always filter: WHERE deleted_at IS NULL
   
   Example:
   ```python
   @property
   def is_deleted(self):
       return self.deleted_at is not None
   ```

4. AUDIT LOGS
   ✅ Log all auth actions: login, password change, token creation
   ✅ Log all destructive operations: DELETE, UPDATE
   ✅ Include: user_id, action, ip_address, timestamp
   
   Example:
   ```python
   def log_action(user_id, action, resource, status):
       audit = AuditLog(
           user_id=user_id,
           action=action,
           resource=resource,
           status=status,
           ip_address=request.client.host
       )
       db.add(audit)
       db.commit()
   ```

5. CONNECTION SECURITY
   ✅ Always use SSL/TLS for PostgreSQL
   ✅ Connection string: postgresql+psycopg2://user:pwd@host/db?sslmode=require
   ✅ Use connection pooling (SQLAlchemy pool_size, max_overflow)

6. QUERY OPTIMIZATION
   ✅ Use indexes on frequently queried columns
   ✅ Lazy load relationships (don't load unnecessary data)
   ✅ Use EXPLAIN ANALYZE to find slow queries

═══════════════════════════════════════════════════════════════════════════════
📦 PHASE 2 DEPENDENCIES TO ADD
═══════════════════════════════════════════════════════════════════════════════

```
# Database ORM
sqlalchemy==2.0.23
psycopg2-binary==2.9.9  # PostgreSQL adapter

# Database Migrations
alembic==1.12.1

# Connection Pooling
sqlalchemy-utils==0.41.1

# Data Validation
pydantic==2.5.0
pydantic[email]==2.5.0
```

Add to requirements.txt:
```
# Phase 2: Database & Persistence
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
sqlalchemy-utils==0.41.1
```

═══════════════════════════════════════════════════════════════════════════════
🐘 POSTGRESQL SETUP INSTRUCTIONS
═══════════════════════════════════════════════════════════════════════════════

Installation (Ubuntu/Debian):
┌──────────────────────────────────────────────────────────────────────────────┐
│ # Install PostgreSQL 15+                                                    │
│ sudo apt-get install postgresql postgresql-contrib                          │
│                                                                              │
│ # Start service                                                             │
│ sudo systemctl start postgresql                                             │
│                                                                              │
│ # Create database & user                                                   │
│ sudo -u postgres psql                                                       │
│ postgres=# CREATE DATABASE aui_email_system;                               │
│ postgres=# CREATE USER aui_dev WITH PASSWORD 'strong_password_here';       │
│ postgres=# GRANT ALL PRIVILEGES ON DATABASE aui_email_system TO aui_dev;   │
│ postgres=# \q                                                               │
│                                                                              │
│ # Connection string for .env                                               │
│ DATABASE_URL=postgresql://aui_dev:strong_password@localhost:5432/aui_email_system
└──────────────────────────────────────────────────────────────────────────────┘

Installation (Docker):
┌──────────────────────────────────────────────────────────────────────────────┐
│ # docker-compose.yml                                                        │
│ version: '3.8'                                                              │
│                                                                              │
│ services:                                                                   │
│   postgres:                                                                 │
│     image: postgres:15-alpine                                              │
│     environment:                                                            │
│       POSTGRES_DB: aui_email_system                                        │
│       POSTGRES_USER: aui_dev                                               │
│       POSTGRES_PASSWORD: strong_password_here                              │
│     ports:                                                                  │
│       - "5432:5432"                                                        │
│     volumes:                                                                │
│       - postgres_data:/var/lib/postgresql/data                            │
│                                                                              │
│ volumes:                                                                    │
│   postgres_data:                                                            │
│                                                                              │
│ # Run                                                                       │
│ docker-compose up -d postgres                                              │
└──────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
💻 CODE EXAMPLES FOR PHASE 2
═══════════════════════════════════════════════════════════════════════════════

1. Create User
────────────────────────────────────────────────────────────────────────────────

```python
from src.database import SessionLocal
from src.models import User
from src.auth import hash_password

def create_user(email: str, password: str, role: str = "user"):
    db = SessionLocal()
    try:
        # Vérifier que l'email n'existe pas
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError(f"User {email} already exists")
        
        # Créer l'utilisateur
        user = User(
            email=email,
            hashed_password=hash_password(password),
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()
```

2. Login User
────────────────────────────────────────────────────────────────────────────────

```python
def login_user(email: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.email == email,
            User.is_active == True
        ).first()
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # Log the login
        audit = AuditLog(
            user_id=user.id,
            action="login",
            status="success"
        )
        db.add(audit)
        db.commit()
        
        return user
    finally:
        db.close()
```

3. Log Email Processing
────────────────────────────────────────────────────────────────────────────────

```python
def log_email_processing(
    user_id: int,
    sender: str,
    subject: str,
    body: str,
    response: str,
    response_time_ms: int
):
    db = SessionLocal()
    try:
        import hashlib
        body_hash = hashlib.sha256(body.encode()).hexdigest()
        
        log = EmailLog(
            user_id=user_id,
            sender=sender,
            subject=subject,
            body=body,
            body_hash=body_hash,
            response=response,
            response_time_ms=response_time_ms,
            status="success",
            model_used="mistral",
            processed_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()
    finally:
        db.close()
```

═══════════════════════════════════════════════════════════════════════════════
📊 BACKUP & RECOVERY STRATEGY
═══════════════════════════════════════════════════════════════════════════════

Daily Backup (cron job):
┌──────────────────────────────────────────────────────────────────────────────┐
│ # /usr/local/bin/backup-postgres.sh                                         │
│                                                                              │
│ #!/bin/bash                                                                 │
│ BACKUP_DIR="/backups/postgres"                                             │
│ DB_NAME="aui_email_system"                                                 │
│ DATE=$(date +%Y%m%d_%H%M%S)                                                │
│                                                                              │
│ mkdir -p $BACKUP_DIR                                                       │
│                                                                              │
│ pg_dump -U aui_dev $DB_NAME | \                                            │
│     gzip > $BACKUP_DIR/${DB_NAME}_${DATE}.sql.gz                           │
│                                                                              │
│ # Keep last 30 days of backups                                             │
│ find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete                       │
│                                                                              │
│ echo "Backup completed: ${DB_NAME}_${DATE}.sql.gz"                         │
│                                                                              │
│ # Crontab entry (daily at 2 AM)                                            │
│ # 0 2 * * * /usr/local/bin/backup-postgres.sh                              │
└──────────────────────────────────────────────────────────────────────────────┘

Restore from Backup:
┌──────────────────────────────────────────────────────────────────────────────┐
│ # Restore the database from backup                                          │
│ gunzip < /backups/postgres/aui_email_system_20240101_020000.sql.gz | \     │
│     psql -U aui_dev aui_email_system                                        │
│                                                                              │
│ # Or with dropdb first                                                     │
│ dropdb -U aui_dev aui_email_system                                          │
│ createdb -U aui_dev aui_email_system                                        │
│ gunzip < backup.sql.gz | psql -U aui_dev aui_email_system                   │
└──────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
✅ PHASE 2 IMPLEMENTATION CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Infrastructure:
  □ Install PostgreSQL 15+
  □ Create database & user
  □ Test connection string
  □ Set up pgAdmin (optional UI)

Code Setup:
  □ Add SQLAlchemy to requirements.txt
  □ Add psycopg2 to requirements.txt
  □ Add Alembic to requirements.txt
  □ Create src/database.py (engine & session)
  □ Create src/models/__init__.py
  □ Create src/models/user.py
  □ Create src/models/email_log.py
  □ Create src/models/rag_document.py
  □ Create src/models/api_token.py
  □ Create src/models/audit_log.py

Migrations:
  □ Initialize Alembic
  □ Create migration for users table
  □ Create migration for email_logs table
  □ Create migration for rag_documents table
  □ Create migration for api_tokens table
  □ Create migration for audit_logs table
  □ Run migrations: alembic upgrade head

Integration:
  □ Update src/auth.py to use User model
  □ Update src/api.py to use database sessions
  □ Create repository/DAO layer
  □ Write tests for database operations
  □ Set up connection pooling

Backup & Recovery:
  □ Create backup script
  □ Test backup restoration
  □ Set up cron job for daily backups
  □ Document disaster recovery plan

═══════════════════════════════════════════════════════════════════════════════

Total Estimated Time for Phase 2: 85 hours (1 week)
Expected Score Improvement: 75 → 85 (+10 points)

Next: Start Phase 2 after Phase 1 tests are passing!
