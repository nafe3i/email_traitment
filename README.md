# AUI Email Support System v2.1

**Système de support email intelligent pour Al Akhawayn University (AUI), Ifrane, Maroc.**

> IA locale (Ollama) · RAG (ChromaDB) · Validation humaine avant envoi · API REST sécurisée

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Flux de traitement](#2-flux-de-traitement)
3. [Ce qui fonctionne / ce qu'il faut configurer](#3-ce-qui-fonctionne--ce-quil-faut-configurer)
4. [Prérequis](#4-prérequis)
5. [Installation](#5-installation)
6. [Configuration externe](#6-configuration-externe)
7. [Démarrage rapide](#7-démarrage-rapide)
8. [API REST](#8-api-rest)
9. [Validation humaine](#9-validation-humaine)
10. [Structure du projet](#10-structure-du-projet)
11. [Knowledge Base](#11-knowledge-base)
12. [Configuration Gmail OAuth2](#12-configuration-gmail-oauth2)
13. [Tests](#13-tests)
14. [Résolution de problèmes](#14-résolution-de-problèmes)

---

## 1. Vue d'ensemble

Le système lit les emails entrants (Gmail ou saisie manuelle), les analyse via un pipeline RAG local, génère une réponse suggérée par Mistral, puis **met cette réponse en attente**. Un administrateur ou un agent (`admin` / `user`) **approuve ou rejette** avant tout envoi Gmail.

### Principes clés

| Principe | Détail |
|----------|--------|
| IA locale | Ollama + Mistral + nomic-embed-text — pas d'API cloud payante |
| Validation humaine | **Aucun envoi automatique** — approbation obligatoire |
| Sécurité | JWT, rôles RBAC, rate limiting, secrets chiffrés |
| Persistance | SQLite (utilisateurs) + JSON (historique) + ChromaDB (vecteurs) |

### Les 8 catégories

| Catégorie | Sujets couverts |
|-----------|-----------------|
| `inscription_admission` | Candidature, admission, réinscription |
| `scolarite_frais` | Frais, paiement, bourse |
| `cours_academique` | Notes, relevés, emploi du temps |
| `it_portail` | MyAUI, Wi-Fi, accès portail |
| `vie_campus` | Résidence, cantine, sport |
| `bibliotheque` | LRC, livres, salles d'étude |
| `stage_carriere` | Stage, emploi, Career Center |
| `general` | Autres demandes |

---

## 2. Flux de traitement

```
Email entrant (Gmail ou POST /emails/process)
        │
        ▼
┌─────────────────────┐
│  EmailDetector      │  Langue · Expéditeur · Urgence · Spam · Doublon
└─────────┬───────────┘
          │ spam / doublon → ignoré
          ▼
┌─────────────────────┐
│  Sanitizer          │  Signatures, citations, URLs, injection prompt (log)
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  Ollama embed       │  Vecteur nomic-embed-text
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  ChromaDB (RAG)     │  Top 3 documents similaires
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  Mistral            │  Catégorisation + génération réponse
└─────────┬───────────┘
          │ confiance ≥ 50 %
          ▼
┌─────────────────────┐
│  File d'attente     │  status: "pending_review"
│  suggested_reply    │  ← réponse IA en attente
└─────────┬───────────┘
          │
    ┌─────┴─────┐
    ▼           ▼
 APPROUVER    REJETER
 POST         POST
 /approve     /reject
    │           │
    ▼           ▼
 Envoi Gmail  status: "rejected"
 status: "sent"   (aucun envoi)
```

### Statuts d'un email

| Statut | Signification |
|--------|---------------|
| `pending_review` | Réponse IA générée, en attente d'un humain |
| `sent` | Approuvé et envoyé via Gmail |
| `rejected` | Rejeté par un humain, non envoyé |
| `approved_no_gmail` | Approuvé mais Gmail non configuré |
| `no_reply_needed` | Confiance insuffisante ou pas de réponse générée |

---

## 3. Ce qui fonctionne / ce qu'il faut configurer

### Fonctionne sans configuration externe (après install Python)

- API REST FastAPI + Swagger `/docs`
- Authentification JWT + rôles (`admin`, `user`, `viewer`)
- Détection email (langue, spam, urgence, doublons)
- Nettoyage et sanitization
- Stockage historique JSON
- Knowledge base (fichiers JSON inclus)
- Tests automatisés (`pytest`)

### Configuration obligatoire dans le projet

| Étape | Commande / fichier |
|-------|-------------------|
| Secrets | Copier `.env.example` → `.env`, remplir `SECRET_KEY` et `JWT_SECRET` |
| Compte admin | `cd src && python seeder.py` |
| Knowledge base vectorielle | `cd src && python seed.py` (nécessite Ollama) |

### Configuration externe (hors code)

| Service | Obligatoire pour… | Installation |
|---------|-------------------|--------------|
| **Ollama** | RAG, catégorisation, génération IA | [ollama.com](https://ollama.com) |
| **Gmail OAuth2** | Lire/envoyer de vrais emails | Google Cloud Console |
| **Compte Gmail** | Boîte surveillée | Compte connecté via OAuth |

> Le projet **ne configure pas** d'adresse email dans le code. C'est la boîte du compte Google authentifié qui est lue (`is:unread`). Pour surveiller `support@aui.ma`, connectez-vous avec ce compte lors de l'OAuth.

---

## 4. Prérequis

| Logiciel | Version | Notes |
|----------|---------|-------|
| Python | 3.10+ | 3.11 recommandé |
| Ollama | Dernière | Pour l'IA locale |
| RAM | 8 GB min | 16 GB recommandé pour Mistral |
| Git | Optionnel | |

---

## 5. Installation

```bash
# 1. Cloner le projet
git clone https://github.com/nafe3i/email_traitment.git
cd email_traitment

# 2. Environnement Python
python -m venv .venv
# Windows :
.venv\Scripts\activate
# macOS / Linux :
source .venv/bin/activate

pip install -r requirements.txt

# 3. Configuration
cp .env.example .env
# Éditer .env — générer les secrets :
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
python -c "import secrets; print(secrets.token_hex(32))"

# 4. Compte administrateur
cd src
python seeder.py

# 5. Modèles Ollama (terminal séparé)
ollama pull mistral
ollama pull nomic-embed-text
ollama serve

# 6. Charger la knowledge base
python seed.py

# 7. Démarrer l'API
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Swagger UI : http://localhost:8000/docs

---

## 6. Configuration externe

### Ollama

```bash
ollama pull mistral
ollama pull nomic-embed-text
ollama serve
# Vérifier :
curl http://localhost:11434/api/tags
```

Variables `.env` : `OLLAMA_BASE`, `OLLAMA_EMBED_MODEL`, `OLLAMA_LLM_MODEL`, `CONFIDENCE_THRESHOLD` (défaut `0.50`).

### Gmail (optionnel — emails réels)

1. Créer un projet sur [Google Cloud Console](https://console.cloud.google.com)
2. Activer **Gmail API**
3. Créer identifiants OAuth2 (Application de bureau)
4. Télécharger → `credentials/credentials.json`
5. Première connexion : `python main.py run` (ouvre le navigateur)
6. Token chiffré sauvegardé dans `credentials/token.json`

Scopes : lecture, envoi, modification des labels (marquer lu).

### Variables `.env` importantes

| Variable | Rôle |
|----------|------|
| `SECRET_KEY` | Chiffrement Fernet du token Gmail |
| `JWT_SECRET` | Signature des tokens API |
| `ALLOWED_REGISTER_DOMAIN` | Inscription limitée (défaut `aui.ma`) |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Compte admin initial (seeder) |
| `GMAIL_CREDENTIALS_PATH` | Chemin credentials Google |
| `ALLOWED_ORIGINS` | CORS pour un futur frontend |

---

## 7. Démarrage rapide

### Mode démo (sans Gmail)

```bash
cd src
python main.py demo
```

### Test API avec authentification

```bash
# 1. Connexion
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@aui.ma","password":"VOTRE_MOT_DE_PASSE"}'

# 2. Traiter un email (remplacer TOKEN)
curl -X POST http://localhost:8000/emails/process \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "student@aui.ma",
    "subject": "Problème Wi-Fi campus",
    "body": "Bonjour, je ne peux plus me connecter au Wi-Fi depuis ce matin."
  }'

# Réponse attendue : "status": "pending_review", "suggested_reply": "..."
```

### Flux validation humaine

```bash
# Lister les emails en attente
curl http://localhost:8000/emails/pending \
  -H "Authorization: Bearer TOKEN"

# Approuver et envoyer
curl -X POST http://localhost:8000/emails/EMAIL_ID/approve \
  -H "Authorization: Bearer TOKEN"

# Rejeter
curl -X POST "http://localhost:8000/emails/EMAIL_ID/reject?reason=Réponse%20incorrecte" \
  -H "Authorization: Bearer TOKEN"
```

---

## 8. API REST

### Endpoints publics

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/health` | Statut serveur, Ollama, ChromaDB |
| `POST` | `/auth/login` | Connexion → JWT |
| `POST` | `/auth/register` | Inscription (`@aui.ma` uniquement) |

### Authentification requise (JWT)

| Méthode | Endpoint | Rôle min | Description |
|---------|----------|----------|-------------|
| `GET` | `/auth/me` | tous | Profil connecté |
| `POST` | `/emails/process` | tous | Traiter un email manuellement |
| `GET` | `/emails/history` | tous | Historique + filtres |
| `GET` | `/emails/{id}` | tous | Détail d'un email |
| `GET` | `/stats` | tous | Statistiques globales |
| `GET` | `/emails/pending` | admin, user | **File d'attente validation** |
| `POST` | `/emails/{id}/approve` | admin, user | **Approuver et envoyer** |
| `POST` | `/emails/{id}/reject` | admin, user | **Rejeter sans envoi** |
| `POST` | `/emails/run` | admin, user | Traiter Gmail non lus |
| `POST` | `/seed` | admin | Recharger knowledge base |
| `DELETE` | `/reset` | admin | Réinitialiser ChromaDB + historique |
| `GET` | `/users` | admin | Lister utilisateurs |
| `PATCH` | `/users/{email}/role` | admin | Changer un rôle |
| `DELETE` | `/users/{email}` | admin | Désactiver un utilisateur |

### Rôles

| Rôle | Permissions |
|------|-------------|
| `admin` | Tout + gestion utilisateurs + seed/reset |
| `user` | Traitement emails + validation humaine + run Gmail |
| `viewer` | Lecture historique et stats uniquement |

### Exemple réponse `POST /emails/process`

```json
{
  "id": "abc123",
  "sender": "student@aui.ma",
  "subject": "Problème Wi-Fi",
  "category": "it_portail",
  "confidence": 0.87,
  "response": "Bonjour,\n\nPour résoudre votre problème de connexion Wi-Fi...",
  "suggested_reply": "Bonjour,\n\nPour résoudre votre problème de connexion Wi-Fi...",
  "status": "pending_review",
  "sent": false,
  "detection": {
    "language": "fr",
    "sender_type": "student",
    "urgency": "normal",
    "should_process": true
  },
  "processed_at": "2026-06-07T12:00:00+00:00"
}
```

> Le paramètre `send_reply` existe encore dans l'API mais **n'envoie plus automatiquement**. Toutes les réponses passent par la file `pending_review`.

---

## 9. Validation humaine

### Vérification dans le code

| Composant | Fichier | Rôle |
|-----------|---------|------|
| Mise en attente | `processor.py` | `status: pending_review` + `suggested_reply` si confiance ≥ 50 % |
| Pas d'envoi auto | `processor.py` | Envoi supprimé du pipeline — uniquement via `/approve` |
| File d'attente | `storage.py` | `get_pending()`, `update_status()` |
| API validation | `api.py` | `/pending`, `/approve`, `/reject` |
| Gmail non lu | `processor.py` | Emails `pending_review` **restent non lus** jusqu'à approbation |

### Workflow recommandé

1. `POST /emails/run` ou `POST /emails/process` → génère des `pending_review`
2. Agent consulte `GET /emails/pending`
3. Lit `suggested_reply` pour chaque email
4. `POST /emails/{id}/approve` → envoi Gmail + `status: sent`
5. Ou `POST /emails/{id}/reject` → `status: rejected` + raison optionnelle

---

## 10. Structure du projet

```
aui_email_system/
├── .env.example              # Template configuration
├── .gitignore
├── requirements.txt
├── README.md
│
├── credentials/              # ⚠️ Ne pas committer
│   ├── credentials.json      # OAuth Google (externe)
│   └── token.json            # Token chiffré (auto-généré)
│
├── data/
│   ├── chroma_db/            # Base vectorielle (auto)
│   ├── reports/report.json   # Historique emails (auto)
│   ├── users/users.db        # SQLite utilisateurs (auto)
│   └── knowledge_base/       # 8 fichiers JSON (80 exemples)
│
├── tests/                    # pytest (14 tests)
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_security.py
│   └── test_sanitizer.py
│
└── src/
    ├── api.py                # API REST FastAPI
    ├── auth.py               # JWT + RBAC
    ├── config.py             # Configuration Pydantic
    ├── database.py           # SQLite utilisateurs
    ├── email_detector.py     # Détection heuristique
    ├── gmail_service.py      # Client Gmail OAuth2
    ├── main.py               # CLI (demo / run)
    ├── models.py             # Modèles SQLAlchemy
    ├── processor.py          # Pipeline RAG + file d'attente
    ├── sanitizer.py          # Nettoyage emails
    ├── secrets.py            # Chiffrement Fernet
    ├── seed.py               # Chargeur ChromaDB
    ├── seeder.py             # Création compte admin
    └── storage.py            # Persistance JSON
```

---

## 11. Knowledge Base

### Format JSON (`data/knowledge_base/*.json`)

```json
[
  {
    "id": "ins_001",
    "category": "inscription_admission",
    "language": "fr",
    "question": "Comment puis-je m'inscrire à AUI ?",
    "answer": "Pour vous inscrire à AUI, vous devez...",
    "tags": ["inscription", "admission"],
    "validated": true
  }
]
```

### Chargement

```bash
cd src
python seed.py           # charge les nouveaux IDs
python seed.py --reset     # vide et recharge tout
# ou API : POST /seed  {"reset_first": true}
```

---

## 12. Configuration Gmail OAuth2

### Étapes Google Cloud

1. [console.cloud.google.com](https://console.cloud.google.com) → Nouveau projet
2. Activer **Gmail API**
3. Écran de consentement OAuth → Type **Externe**
4. Utilisateurs test → ajouter votre email Gmail
5. Identifiants → **Application de bureau** → Télécharger JSON
6. Placer dans `credentials/credentials.json`

### Première authentification

```bash
cd src
python main.py run
```

Le navigateur s'ouvre → autoriser → `credentials/token.json` créé (chiffré avec `SECRET_KEY`).

### Quels emails sont traités ?

- Requête Gmail : `is:unread` (non lus uniquement)
- Limite : `max_emails` (API) ou `--limit` (CLI)
- Doublons ignorés (ID déjà dans l'historique)
- Marqué **lu** seulement après traitement réussi ou après **approbation**

---

## 13. Tests

```bash
# Windows (encodage UTF-8)
set PYTHONUTF8=1
pytest tests/ -v
```

**14 tests** couvrent : auth, hashage mots de passe, inscription `@aui.ma`, CORS, rate limiting, sanitizer.

---

## 14. Résolution de problèmes

### Ollama ne répond pas

```bash
ollama serve
curl http://localhost:11434/api/tags
```

Symptôme : `"error": "ollama_embed_failed"` → catégorisation par mots-clés uniquement.

### ChromaDB vide

```bash
cd src && python seed.py
```

### Token Gmail expiré

```bash
# Supprimer et se reconnecter
del credentials\token.json   # Windows
python main.py run
```

### Aucun email en `pending_review`

- Vérifier que Ollama tourne et que `seed.py` a été exécuté
- La confiance doit être ≥ `CONFIDENCE_THRESHOLD` (0.50 par défaut)
- Emails spam/doublons sont ignorés avant génération

### API ne démarre pas — secrets manquants

```
SECRET_KEY et JWT_SECRET sont obligatoires dans .env
```

### Tests échouent sur Windows

```bash
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
pytest tests/ -v
```

---

## État actuel (v2.1)

| Fonctionnalité | Statut |
|----------------|--------|
| Pipeline RAG Ollama + ChromaDB | ✅ |
| Détection email intelligente | ✅ |
| API REST + JWT + RBAC | ✅ |
| **Validation humaine avant envoi** | ✅ |
| Chiffrement token Gmail | ✅ |
| Rate limiting | ✅ |
| Tests pytest | ✅ (14/14) |
| Interface web admin | ❌ À venir |
| Webhooks Gmail (push) | ❌ Polling manuel |
| Notifications pending | ❌ À venir |

---

## Licence & contact

Développé pour **Al Akhawayn University (AUI)**, Ifrane, Maroc.

- Documentation interactive : http://localhost:8000/docs
- Dépôt : https://github.com/nafe3i/email_traitment

---

*AUI Email Support System — Ollama · Mistral · ChromaDB · FastAPI · Validation humaine*
