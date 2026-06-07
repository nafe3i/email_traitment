"""
database.py — Engine SQLAlchemy + Session + CRUD users.
DB : data/users/users.db (SQLite)
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models import Base, User, RoleEnum

DB_PATH      = Path(__file__).parent.parent / "data" / "users" / "users.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine       = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_user(db: Session, email: str, hashed_password: str, role: str = "viewer") -> User:
    if get_user_by_email(db, email):
        raise ValueError(f"Un utilisateur avec l'email '{email}' existe deja.")

    user = User(
        id              = f"usr_{uuid.uuid4().hex[:8]}",
        email           = email.lower().strip(),
        hashed_password = hashed_password,
        role            = RoleEnum(role),
        is_active       = True,
        created_at      = datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower().strip()).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_all_users(db: Session) -> list:
    return [u.to_dict() for u in db.query(User).all()]


def update_last_login(db: Session, email: str) -> None:
    user = get_user_by_email(db, email)
    if user:
        user.last_login = datetime.now(timezone.utc)
        db.commit()


def update_user_role(db: Session, email: str, new_role: str) -> bool:
    user = get_user_by_email(db, email)
    if not user:
        return False
    user.role = RoleEnum(new_role)
    db.commit()
    return True


def deactivate_user(db: Session, email: str) -> bool:
    user = get_user_by_email(db, email)
    if not user:
        return False
    user.is_active = False
    db.commit()
    return True


def delete_user(db: Session, email: str) -> bool:
    user = get_user_by_email(db, email)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True
