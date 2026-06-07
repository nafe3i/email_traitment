"""
main.py — Entrée CLI principale pour AUI Email Support System.
Permet d'exécuter des démonstrations locales ou de lancer le traitement réel des e-mails Gmail.
"""

import sys
import argparse
import logging
from pathlib import Path

# Ajoute le dossier src au chemin de recherche pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from processor import EmailProcessor
from storage import Storage
from config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Exemples d'e-mails pour le mode démo représentant des cas réels du campus de l'AUI
DEMO_EMAILS = [
    {
        "id": "demo_001",
        "sender": "student_test@aui.ma",
        "subject": "Problème d'accès MyAUI et WiFi",
        "body": "Bonjour, je n'arrive pas à me connecter au WiFi du campus ni à mon compte MyAUI. Pouvez-vous réinitialiser mon mot de passe s'il vous plaît ? Mon ID étudiant est 98765. Merci !",
    },
    {
        "id": "demo_002",
        "sender": "candidate@gmail.com",
        "subject": "Admission requirements for Fall 2026",
        "body": "Dear Admissions Office, I am planning to apply for the Computer Science program next semester. Could you please send me the admission requirements and the tuition fees details? Best regards.",
    },
    {
        "id": "demo_003",
        "sender": "parent_alami@yahoo.fr",
        "subject": "Frais de scolarité et facture",
        "body": "Bonjour, je suis le tuteur de l'étudiante Salma Alami. Je souhaiterais savoir comment régler les frais du semestre et à qui envoyer le justificatif de virement. Merci pour votre aide.",
    },
    {
        "id": "demo_004",
        "sender": "staff_member@aui.ma",
        "subject": "Mohammed VI Library room booking request",
        "body": "Hi LRC Support, I need to book a study room for a group of 4 students tomorrow from 2 PM to 5 PM. Is there any room available in the library? Thanks.",
    }
]


def run_demo():
    """Exécute le traitement sur 4 e-mails factices pour valider le pipeline RAG/LLM local."""
    print("\n" + "="*60)
    print("🚀 DÉMARRAGE DU MODE DÉMONSTRATION (Local)")
    print("="*60)
    print("Vérification et chargement de la base vectorielle ChromaDB...")
    
    storage = Storage()
    # gmail_service est None car nous n'envoyons rien
    processor = EmailProcessor(gmail_service=None, storage=storage)
    
    for i, em in enumerate(DEMO_EMAILS, 1):
        print(f"\n[{i}/4] 📨 E-mail Reçu : '{em['subject']}' (de: {em['sender']})")
        
        # Exécuter le traitement
        res = processor.process_email(
            email_id=em["id"],
            sender=em["sender"],
            subject=em["subject"],
            body=em["body"],
            send_reply=False
        )
        
        print(f"  👉 Catégorie détectée  : {res['category']} (Confiance: {res['confidence']})")
        print(f"  👉 Langue & Urgence    : {res['detection']['language']} | {res['detection']['urgency']}")
        print(f"  👉 Réponse Suggérée    :\n{'-'*40}\n{res['response']}\n{'-'*40}")
        if res.get("error"):
            print(f"  ⚠️  Information/Dégradation : {res['error']}")
            
    print("\n" + "="*60)
    print("✅ FIN DE LA DÉMONSTRATION")
    print("="*60 + "\n")


def run_gmail_integration(send_reply: bool, max_emails: int):
    """Se connecte à Gmail, lit les e-mails non lus, et y répond (si configuré)."""
    print("\n" + "="*60)
    print("✉️ DÉMARRAGE DU TRAITEMENT DES E-MAILS REELS (Gmail API)")
    print("="*60)
    
    try:
        from gmail_service import get_gmail_service, fetch_unread_emails
    except ImportError as e:
        logger.error(f"Erreur d'importation du module gmail_service: {e}")
        print("❌ Impossible de charger gmail_service.py. Assurez-vous d'avoir installé les packages requis.")
        return

    try:
        service = get_gmail_service()
        print("✓ Connexion OAuth2 sécurisée établie avec l'API Gmail.")
    except Exception as e:
        logger.exception("Échec d'initialisation du service Gmail")
        print(f"❌ Erreur de connexion Gmail : {e}")
        return

    print("Recherche des e-mails non lus dans la boîte de réception...")
    emails = fetch_unread_emails(service, max_results=max_emails)
    print(f"✓ {len(emails)} e-mails non lus trouvés.")
    
    if not emails:
        print("Aucun e-mail à traiter.")
        return

    storage = Storage()
    processor = EmailProcessor(gmail_service=service, storage=storage)
    
    for i, em in enumerate(emails, 1):
        print(f"\n[{i}/{len(emails)}] 📨 Email de : {em['sender']} | Sujet: {em['subject']}")
        res = processor.process_email(
            email_id=em["id"],
            sender=em["sender"],
            subject=em["subject"],
            body=em["body"],
            send_reply=send_reply
        )
        print(f"  👉 Catégorie détectée : {res['category']} | Confiance: {res['confidence']}")
        print(f"  👉 Envoi de la réponse : {'OUI (Réponse envoyée)' if res['sent'] else 'NON (Simulation / Confiance faible)'}")
        if res.get("error"):
            print(f"  ⚠️  Erreur : {res['error']}")

    print("\n" + "="*60)
    print("✅ PROCESSUS DE TRAITEMENT GMAIL TERMINÉ")
    print("="*60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AUI Email Support System CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Commande demo
    subparsers.add_parser("demo", help="Lancer le traitement sur les 4 e-mails factices locaux")
    
    # Commande run
    run_parser = subparsers.add_parser("run", help="Se connecter à Gmail et traiter les messages non lus")
    run_parser.add_argument("--send-reply", action="store_true", help="Activer l'envoi effectif des réponses par e-mail")
    run_parser.add_argument("--limit", type=int, default=20, help="Nombre maximum d'e-mails à traiter")
    
    args = parser.parse_args()
    
    if args.command == "demo":
        run_demo()
    elif args.command == "run":
        run_gmail_integration(send_reply=args.send_reply, max_emails=args.limit)
