"""Sécurité : hachage des mots de passe, JWT, vérification de la clé d'ingestion IA."""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """Retourne le `sub` (identifiant utilisateur) ou None si invalide."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None


def verify_ingest_key(provided: str | None) -> bool:
    """Authentifie le pipeline `ai/` via une clé partagée (header X-AI-Key)."""
    # TODO(dev): remplacer par une vraie signature HMAC par événement si besoin.
    return bool(provided) and provided == settings.ai_ingest_api_key
