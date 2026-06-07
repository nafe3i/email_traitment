"""
auth.py — JWT Authentication & Authorization System
Stockage : SQLite via SQLAlchemy (data/users/users.db)
Roles    : admin > user > viewer (viewer par defaut a l inscription)
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db, create_user, get_user_by_email, update_last_login
from config import settings

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security    = HTTPBearer()

ALGORITHM                 = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
SECRET_KEY                = settings.JWT_SECRET


class TokenData(BaseModel):
    user_id: str
    email:   str
    role:    str

class User(BaseModel):
    id:         str
    email:      EmailStr
    role:       str  = "viewer"
    is_active:  bool = True
    created_at: str  = ""
    last_login: str  = ""

class UserCreate(BaseModel):
    email:    EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email:    EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int
    user:         User


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire    = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        email   = payload.get("email")
        role    = payload.get("role", "viewer")
        if not user_id or not email:
            return None
        return TokenData(user_id=user_id, email=email, role=role)
    except JWTError:
        return None


def _make_user(u) -> User:
    return User(
        id         = u.id,
        email      = u.email,
        role       = u.role.value,
        is_active  = u.is_active,
        created_at = u.created_at.isoformat() if u.created_at else "",
        last_login = u.last_login.isoformat() if u.last_login else "",
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token_data = verify_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expire.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user_by_email(db, token_data.email)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur inactif ou supprime.")
    return _make_user(user)


def require_role(allowed_roles: List[str]):
    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db),
    ) -> User:
        user = await get_current_user(credentials, db)
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissions insuffisantes. Roles requis : {allowed_roles}",
            )
        return user
    return role_checker


def register_user(db: Session, user_create: UserCreate) -> User:
    u = create_user(
        db              = db,
        email           = user_create.email,
        hashed_password = hash_password(user_create.password),
        role            = "viewer",
    )
    return _make_user(u)


def login_user(db: Session, user_login: UserLogin) -> Optional[TokenResponse]:
    user = get_user_by_email(db, user_login.email)
    if not user or not user.is_active:
        return None
    if not verify_password(user_login.password, user.hashed_password):
        return None
    update_last_login(db, user_login.email)
    token = create_access_token({
        "user_id": user.id,
        "email":   user.email,
        "role":    user.role.value,
    })
    return TokenResponse(
        access_token = token,
        expires_in   = ACCESS_TOKEN_EXPIRE_HOURS * 3600,
        user         = _make_user(user),
    )
