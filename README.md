# AUI Email Support System v2.0

**Système intelligent d'automatisation du support email pour Al Akhawayn University (AUI), Ifrane, Maroc.**

> 100% local · Aucune API externe · Zéro coût d'utilisation

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture technique](#2-architecture-technique)
3. [Prérequis](#3-prérequis)
4. [Installation pas-à-pas](#4-installation-pas-à-pas)
5. [Structure du projet](#5-structure-du-projet)
6. [Démarrage rapide](#6-démarrage-rapide)
7. [Utilisation de l'API REST](#7-utilisation-de-lapi-rest)
8. [Modules détaillés](#8-modules-détaillés)
9. [Knowledge Base — Format JSON](#9-knowledge-base--format-json)
10. [Configuration Gmail OAuth2](#10-configuration-gmail-oauth2)
11. [Résolution de problèmes](#11-résolution-de-problèmes)
12. [Feuille de route](#12-feuille-de-route)

---

## 1. Vue d'ensemble

Le AUI Email Support System connecte à la boîte Gmail de l'université, lit les emails entrants des étudiants et parents, les analyse intelligemment, et génère des réponses professionnelles personnalisées — le tout via un LLM local (Mistral 7B via Ollama).

### Ce que fait le système

```
Email entrant (Gmail)
        │
        ▼
┌─────────────────────┐
│  EmailDetector      │  Langue / Type expéditeur / Urgence / Spam / Doublon
└─────────┬───────────┘
          │ is_spam? → ignorer
          │ is_duplicate? → ignorer
          ▼
┌─────────────────────┐
│  Nettoyage corps    │  Supprime signatures, citations, URLs
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  nomic-embed-text   │  Vecteur 768 dimensions
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  ChromaDB           │  Top 3 emails similaires (cosinus)
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  Mistral 7B         │  Catégorisation (8 catégories)
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  Mistral 7B         │  Génération réponse professionnelle
└─────────┬───────────┘
          │ confiance > 50% + send_reply=True
          ▼
┌─────────────────────┐
│  Gmail API          │  Envoi automatique
└─────────┬───────────┘
          ▼
┌─────────────────────┐
│  ChromaDB + JSON    │  Auto-enrichissement + persistance
└─────────────────────┘
```

### Les 8 catégories traitées

| Catégorie | Sujets couverts |
|-----------|-----------------|
| `inscription_admission` | Candidature, admission, réinscription, transfert |
| `scolarite_frais` | Frais, paiement, bourse, aide financière |
| `cours_academique` | Notes, relevés, emploi du temps, crédits |
| `it_portail` | MyAUI, Wi-Fi, email universitaire, accès |
| `vie_campus` | Résidence, cantine, sport, associations |
| `bibliotheque` | LRC, bases de données, réservation salle |
| `stage_carriere` | Stage, emploi, recommandation, Career Center |
| `general` | Autres demandes |

---

## 2. Architecture technique

### Stack

| Composant | Rôle | Port |
|-----------|------|------|
| **Python 3.11+** | Langage principal | — |
| **Ollama + Mistral 7B** | LLM local : catégorisation + génération | 11434 |
| **nomic-embed-text** | Embeddings 768D | 11434 |
| **ChromaDB** | Base vectorielle persistante | — |
| **FastAPI + Uvicorn** | API REST avec Swagger | 8000 |
| **Gmail API (OAuth2)** | Lecture et envoi d'emails | — |

### Fichiers principaux

```
src/
├── email_detector.py  — Détection intelligente (langue, urgence, spam…)
├── processor.py       — Pipeline RAG complet
├── storage.py         — Persistance JSON (report.json)
├── seed.py            — Chargement knowledge base → ChromaDB
└── api.py             — API REST FastAPI (8 endpoints)
```

### Flux de données détaillé

**RAG (Retrieval-Augmented Generation)** :
1. L'email brut est nettoyé (suppression signatures/citations)
2. `nomic-embed-text` génère un vecteur 768D du texte
3. ChromaDB trouve les 3 emails les plus similaires (similarité cosinus)
4. Ces 3 emails sont injectés comme contexte dans le prompt Mistral
5. Mistral catégorise → une 2ème recherche filtrée par catégorie est faite
6. Mistral génère une réponse basée sur les exemples de réponses similaires
7. Score de confiance = similarité du document le plus proche (0.0–1.0)
8. Si confiance > 0.50 et `send_reply=True` → envoi Gmail automatique
9. Email indexé dans ChromaDB → la base s'enrichit automatiquement

---

## 3. Prérequis

### Logiciels requis

| Logiciel | Version min | Installation |
|----------|-------------|--------------|
| Python | 3.11+ | [python.org](https://python.org) |
| Ollama | Dernière | [ollama.ai](https://ollama.ai) |
| Git | Toute | optionnel |

### Ressources matérielles recommandées

| Composant | Minimum | Recommandé |
|-----------|---------|------------|
| RAM | 8 GB | 16 GB |
| Stockage | 10 GB libres | 20 GB |
| CPU | 4 cœurs | 8 cœurs |
| GPU | optionnel | NVIDIA 6GB+ (x5 plus rapide) |

> **Note** : Le système fonctionne entièrement sur CPU. Un GPU accélère Ollama mais n'est pas obligatoire.

---

## 4. Installation pas-à-pas

### Étape 1 — Installer Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows : télécharger l'installeur sur https://ollama.ai/download
```

Vérifier qu'Ollama tourne :
```bash
ollama --version
# Doit afficher : ollama version X.X.X
```

### Étape 2 — Télécharger les modèles

```bash
# Modèle LLM principal (4.1 GB)
ollama pull mistral

# Modèle d'embeddings (274 MB)
ollama pull nomic-embed-text
```

Vérification :
```bash
ollama list
# Doit afficher mistral et nomic-embed-text
```

### Étape 3 — Cloner et configurer le projet

```bash
git clone <URL_DU_REPO> aui-email-support
cd aui-email-support
```

### Étape 4 — Environnement Python

```bash
# Créer un environnement virtuel (recommandé)
python -m venv .venv

# Activer l'environnement
# macOS / Linux :
source .venv/bin/activate
# Windows :
.venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### Étape 5 — Configurer Gmail OAuth2

Voir la section [10. Configuration Gmail OAuth2](#10-configuration-gmail-oauth2) pour les instructions détaillées.

En résumé :
1. Créer un projet Google Cloud
2. Activer l'API Gmail
3. Télécharger `credentials.json` → le placer dans `credentials/`

### Étape 6 — Charger la knowledge base

```bash
cd src
python seed.py
```

Résultat attendu :
```
INFO ✓ ins_001 [inscription_admission]
INFO ✓ ins_002 [inscription_admission]
...
INFO Knowledge base chargée : 80 nouveaux documents.
INFO Total collection : 80 documents.
```

### Étape 7 — Lancer le système

**Option A : API REST (recommandée pour l'intégration)**
```bash
cd src
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```
Accéder au Swagger UI : http://localhost:8000/docs

**Option B : CLI (traitement en lot)**
```bash
cd src
python main.py demo    # Test avec 4 emails fictifs
python main.py run     # Traite les vrais emails Gmail
```

---

## 5. Structure du projet

```
aui-email-support/
│
├── README.md                          ← Ce fichier
├── requirements.txt                   ← Dépendances Python
├── .gitignore                         ← Exclut credentials et chroma_db
│
├── credentials/
│   ├── LISEZ_MOI.txt                  ← Instructions OAuth2
│   ├── credentials.json               ← ⚠️ Votre clé Google (NE PAS committer)
│   └── token.json                     ← ⚠️ Token OAuth2 (généré auto)
│
├── data/
│   ├── chroma_db/                     ← Base vectorielle ChromaDB (générée)
│   ├── reports/
│   │   └── report.json                ← Historique de tous les emails traités
│   └── knowledge_base/
│       ├── inscription_admission.json  ← 10 exemples
│       ├── scolarite_frais.json        ← 10 exemples
│       ├── cours_academique.json       ← 10 exemples
│       ├── it_portail.json             ← 10 exemples
│       ├── vie_campus.json             ← 10 exemples
│       ├── bibliotheque.json           ← 10 exemples
│       ├── stage_carriere.json         ← 10 exemples
│       └── general.json               ← 10 exemples
│                                         TOTAL : 80 exemples validés
│
└── src/
    ├── email_detector.py              ← Détection intelligente des emails
    ├── processor.py                   ← Pipeline RAG principal
    ├── storage.py                     ← Persistance JSON
    ├── seed.py                        ← Chargeur knowledge base
    ├── api.py                         ← API REST FastAPI
    ├── gmail_service.py               ← Client Gmail OAuth2 (existant)
    └── main.py                        ← CLI (existant, non modifié)
```

---

## 6. Démarrage rapide

### Test immédiat sans Gmail (mode demo)

```bash
cd src
python main.py demo
```

### Test de l'API

```bash
# Terminal 1 : démarrer l'API
cd src && uvicorn api:app --port 8000

# Terminal 2 : tester
curl http://localhost:8000/health

# Traiter un email de test
curl -X POST http://localhost:8000/emails/process \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "student@aui.ma",
    "subject": "Demande de relevé de notes",
    "body": "Bonjour, je souhaite obtenir mon relevé de notes officiel pour le semestre dernier. Merci."
  }'
```

### Interface Swagger interactive

Ouvrir http://localhost:8000/docs dans votre navigateur.

---

## 7. Utilisation de l'API REST

### Endpoints disponibles

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/health` | Statut serveur + Ollama + ChromaDB |
| `POST` | `/emails/process` | Traiter un email manuellement |
| `POST` | `/emails/run` | Traiter les emails Gmail non lus |
| `GET` | `/emails/history` | Historique complet |
| `GET` | `/emails/{id}` | Détail d'un email |
| `GET` | `/stats` | Statistiques globales |
| `POST` | `/seed` | Recharger la knowledge base |
| `DELETE` | `/reset` | Réinitialiser tout |

---

### GET /health

Vérifie que tous les composants sont opérationnels.

**Réponse :**
```json
{
  "status": "ok",
  "ollama": true,
  "chroma": {
    "collection": "email_support",
    "documents": 80,
    "path": "./data/chroma_db"
  },
  "storage": {
    "path": "./data/reports/report.json",
    "total": 42
  }
}
```

---

### POST /emails/process

Traite un email et retourne le résultat complet.

**Corps de la requête :**
```json
{
  "id": "optionnel-sera-généré-auto",
  "sender": "ab12345@aui.ma",
  "subject": "Problème de connexion Wi-Fi",
  "body": "Bonjour, je n'arrive plus à me connecter au Wi-Fi du campus depuis ce matin. Mon identifiant est ab12345. Merci de l'aide.",
  "send_reply": false
}
```

**Réponse :**
```json
{
  "id": "a1b2c3d4",
  "sender": "ab12345@aui.ma",
  "subject": "Problème de connexion Wi-Fi",
  "body_clean": "Bonjour, je n'arrive plus à me connecter au Wi-Fi...",
  "detection": {
    "language": "fr",
    "sender_type": "student",
    "urgency": "normal",
    "spam_reason": "not_spam",
    "is_spam": false,
    "is_duplicate": false,
    "priority_score": 60,
    "flags": [],
    "should_process": true
  },
  "category": "it_portail",
  "confidence": 0.87,
  "response": "Bonjour,\n\nNous avons bien reçu votre signalement...",
  "sent": false,
  "error": null,
  "processed_at": "2024-01-15T10:30:00Z",
  "processing_ms": 4200
}
```

---

### POST /emails/run

Déclenche le traitement automatique de la boîte Gmail.

**Corps :**
```json
{
  "max_emails": 20,
  "send_reply": false
}
```

**Réponse :**
```json
{
  "processed": 5,
  "sent": 3,
  "skipped": 2,
  "results": [ ... ]
}
```

---

### GET /emails/history

Retourne l'historique avec filtres optionnels.

**Paramètres de requête :**
- `limit` : nombre max de résultats (défaut: 50)
- `category` : filtrer par catégorie (ex: `it_portail`)
- `language` : filtrer par langue (`fr`, `en`, `ar`)

```bash
# Exemples
GET /emails/history?limit=10
GET /emails/history?category=scolarite_frais
GET /emails/history?language=en&limit=20
```

---

### GET /stats

```json
{
  "total": 127,
  "sent": 98,
  "avg_confidence": 0.823,
  "by_category": {
    "it_portail": 34,
    "scolarite_frais": 28,
    "cours_academique": 22,
    "inscription_admission": 18,
    "vie_campus": 12,
    "stage_carriere": 8,
    "bibliotheque": 3,
    "general": 2
  },
  "by_language": { "fr": 89, "en": 38 },
  "by_urgency": { "normal": 95, "high": 22, "low": 10 },
  "chroma": { "documents": 207, "collection": "email_support" }
}
```

---

### POST /seed

Recharge la knowledge base depuis `data/knowledge_base/*.json`.

```json
{ "reset_first": false }
```

`reset_first: true` → vide ChromaDB avant de recharger (utile si vous avez modifié les exemples).

---

### DELETE /reset

⚠️ **Attention** : efface toute la base vectorielle ET tout l'historique.

```bash
curl -X DELETE http://localhost:8000/reset
```

---

## 8. Modules détaillés

### email_detector.py

Analyse un email de manière purement heuristique (pas de LLM = rapide, gratuit).

```python
from email_detector import EmailDetector

detector = EmailDetector(processed_ids=set())
result = detector.detect(
    email_id="abc123",
    sender="student@aui.ma",
    subject="URGENT - Mon compte bloqué",
    body="Bonjour, mon accès MyAUI est bloqué depuis ce matin..."
)

print(result.language)       # Language.FRENCH
print(result.urgency)        # UrgencyLevel.HIGH
print(result.sender_type)    # SenderType.STUDENT
print(result.priority_score) # 90
print(result.should_process) # True
print(result.flags)          # ["urgent"]
```

**Logique de score de priorité (0-100) :**
- Base : 50
- Urgence HIGH : +30
- Urgence LOW : −20
- Expéditeur étudiant : +10
- Expéditeur parent : +5
- Expéditeur externe : −10
- Spam : → 0 (plancher immédiat)

---

### processor.py

Le cœur du système — orchestre tout le pipeline.

```python
from processor import EmailProcessor
from storage import Storage

storage = Storage()
proc    = EmailProcessor(gmail_service=None, storage=storage)

result = proc.process_email(
    email_id   = "test_001",
    sender     = "parent@gmail.com",
    subject    = "Frais de scolarité de mon fils",
    body       = "Bonjour, mon fils Ahmed est en L2 informatique...",
    send_reply = False,
)
```

**Comportement en cas de panne Ollama :**
- `embed()` échoue → `_fallback_category()` utilise des règles heuristiques (mots-clés)
- `generate()` échoue → réponse de fallback statique en français/anglais
- Le système ne plante jamais, il dégrade gracieusement

---

### storage.py

Persistance des résultats dans `data/reports/report.json`.

```python
from storage import Storage

storage = Storage()

# Sauvegarder
storage.save_email({"id": "x", "category": "it_portail", ...})

# Lire
email  = storage.get_by_id("x")
all    = storage.get_all()
stats  = storage.get_stats()

# IDs déjà traités (pour le détecteur de doublons)
ids    = storage.get_processed_ids()
```

---

### seed.py

Charge les fichiers JSON de la knowledge base dans ChromaDB.

```bash
# Chargement initial
python seed.py

# Rechargement complet (après modification des JSON)
python seed.py --reset
```

**Format attendu des fichiers JSON** : voir section 9.

---

## 9. Knowledge Base — Format JSON

Chaque fichier dans `data/knowledge_base/` doit suivre ce format :

```json
[
  {
    "id": "ins_001",
    "category": "inscription_admission",
    "language": "fr",
    "question": "Comment puis-je m'inscrire à AUI ?",
    "answer": "Pour vous inscrire à AUI, vous devez...",
    "tags": ["inscription", "admission", "dossier"],
    "validated": true
  }
]
```

### Champs obligatoires

| Champ | Type | Description |
|-------|------|-------------|
| `id` | string | Identifiant unique (ex: `ins_001`) |
| `category` | string | Une des 8 catégories exactes |
| `language` | string | `"fr"` ou `"en"` |
| `question` | string | Question type (texte de recherche) |
| `answer` | string | Réponse modèle utilisée par le LLM |
| `tags` | array | Mots-clés pour debug/analyse |
| `validated` | boolean | `false` = ignoré au chargement |

### Conseils pour de bons exemples

1. **Variez les formulations** : même question en plusieurs styles (formel, informel, avec fautes)
2. **Équilibrez les langues** : environ 50/50 français/anglais par catégorie
3. **Réponses complètes** : incluez des informations concrètes (emails, URLs, délais)
4. **Définissez `validated: false`** pour les exemples en cours de rédaction

### Ajouter de nouveaux exemples

1. Éditez ou créez un fichier JSON dans `data/knowledge_base/`
2. Rechargez : `python seed.py` (ne recharge que les nouveaux IDs)
3. Pour tout recharger : `python seed.py --reset`
4. Via l'API : `POST /seed` avec `{"reset_first": true}`

---

## 10. Configuration Gmail OAuth2

### Étape 1 — Créer un projet Google Cloud

1. Allez sur https://console.cloud.google.com
2. Cliquez "Nouveau projet" → nommez-le `AUI-Email-Support`
3. Sélectionnez votre projet

### Étape 2 — Activer l'API Gmail

1. Menu gauche → "APIs et services" → "Bibliothèque"
2. Recherchez "Gmail API"
3. Cliquez "Activer"

### Étape 3 — Configurer l'écran de consentement

1. "APIs et services" → "Écran de consentement OAuth"
2. Type : **Externe** → Créer
3. Nom de l'application : `AUI Email Support`
4. Email support : votre email
5. Enregistrer et continuer (les autres étapes sont optionnelles)
6. Section "Utilisateurs test" → ajoutez votre email Gmail

### Étape 4 — Créer les identifiants OAuth2

1. "APIs et services" → "Identifiants"
2. "+ Créer des identifiants" → "ID client OAuth"
3. Type d'application : **Application de bureau**
4. Nom : `AUI Desktop Client`
5. Créer → Télécharger le JSON
6. Renommer le fichier en `credentials.json`
7. Le placer dans `credentials/credentials.json`

### Étape 5 — Première connexion

```bash
cd src
python main.py demo
```

Un navigateur s'ouvrira automatiquement pour l'autorisation Google.
Acceptez → `credentials/token.json` est créé automatiquement.

### Droits d'accès Gmail configurés

Le système demande uniquement :
- `gmail.readonly` — lire les emails non lus
- `gmail.send` — envoyer des réponses (uniquement si `send_reply=True`)
- `gmail.modify` — marquer les emails comme lus après traitement

---

## 11. Résolution de problèmes

### Ollama ne répond pas

```
Symptôme : "ollama_embed_failed" dans les résultats
```

```bash
# Vérifier qu'Ollama tourne
ollama list
ollama serve  # si le service n'est pas démarré

# Tester manuellement
curl http://localhost:11434/api/tags
```

---

### ChromaDB — erreur de collection

```
Symptôme : "Collection 'email_support' not found"
```

```bash
# Recharger la knowledge base
cd src && python seed.py

# Ou via l'API
curl -X POST http://localhost:8000/seed -H "Content-Type: application/json" -d '{}'
```

---

### Gmail — token expiré

```
Symptôme : "invalid_grant" ou "Token has been expired or revoked"
```

```bash
# Supprimer le token et se reconnecter
rm credentials/token.json
python src/main.py demo  # re-génère le token
```

---

### Confiance toujours faible (< 50%)

La base vectorielle est trop petite. Solutions :
1. Rechargez la knowledge base : `python seed.py --reset`
2. Traitez plus d'emails en mode run (ils s'auto-indexent)
3. Ajoutez plus d'exemples dans `data/knowledge_base/`

---

### L'API ne démarre pas (port 8000 occupé)

```bash
# Utiliser un autre port
uvicorn api:app --port 8001

# Ou tuer le processus
lsof -ti:8000 | xargs kill -9
```

---

### Mémoire insuffisante pour Mistral

Mistral 7B nécessite ~4 GB de RAM pour les poids. Si votre machine est limitée :

```bash
# Utiliser un modèle plus léger
ollama pull phi3:mini    # 2.3 GB

# Modifier OLLAMA_MODEL dans processor.py
LLM_MODEL = "phi3:mini"
```

---

## 12. Feuille de route

### v2.0 (actuelle)
- [x] EmailDetector (langue, urgence, spam, doublon, priorité)
- [x] Knowledge Base structurée (80 exemples, 8 catégories)
- [x] Pipeline RAG amélioré (nettoyage, timeout, fallback)
- [x] Storage persistant (report.json)
- [x] API REST complète (8 endpoints)

### v2.1 (prochaine)
- [ ] Interface web d'administration (dashboard React)
- [ ] Métriques en temps réel (Prometheus + Grafana)
- [ ] Support arabe complet (modèle embedding spécialisé)
- [ ] Tests unitaires (pytest)

### v3.0 (futur)
- [ ] Multi-boîtes Gmail (plusieurs départements)
- [ ] Apprentissage actif (feedback humain améliore le modèle)
- [ ] Support WhatsApp Business API
- [ ] Export Excel des statistiques

---

## Licence & Contacts

Développé pour **Al Akhawayn University (AUI)**, Ifrane, Maroc.

Pour toute question technique sur ce système :
- Ouvrez une issue GitHub
- Consultez le Swagger UI : http://localhost:8000/docs

---

*AUI Email Support System — Propulsé par Ollama · Mistral 7B · ChromaDB · FastAPI*
