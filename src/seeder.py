"""
seeder.py — Initialise la base avec le compte admin par defaut.

Usage :
    python seeder.py
    python seeder.py --reset   # supprime tout et recrée
"""

import sys
import os
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from passlib.context import CryptContext
from database import init_db, create_user, get_all_users, delete_user, SessionLocal

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger  = logging.getLogger(__name__)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def run_seeder(reset: bool = False) -> None:
    init_db()
    db = SessionLocal()

    try:
        if reset:
            for user in get_all_users(db):
                delete_user(db, user["email"])
            logger.info("Base utilisateurs videe.")

        admin_email    = os.getenv("ADMIN_EMAIL", "admin@aui.ma")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123456")

        try:
            create_user(
                db              = db,
                email           = admin_email,
                hashed_password = pwd_ctx.hash(admin_password),
                role            = "admin",
            )
            logger.info(f"Admin cree : {admin_email}")
        except ValueError:
            logger.info(f"Admin existe deja : {admin_email}")

        logger.info("Utilisateurs en base :")
        for u in get_all_users(db):
            logger.info(f"  {u['email']} | {u['role']} | active: {u['is_active']}")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Vider la base avant de seeder")
    args = parser.parse_args()
    run_seeder(reset=args.reset)
