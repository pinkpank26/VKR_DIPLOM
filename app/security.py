import time
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: int, role: str) -> str:
    now = int(time.time())
    payload = {
        "iss": settings.APP_JWT_ISSUER,
        "iat": now,
        "exp": now + settings.APP_JWT_EXPIRE_MIN * 60,
        "sub": str(user_id),
        "role": role,
    }
    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.APP_SECRET_KEY,
            algorithms=["HS256"],
            issuer=settings.APP_JWT_ISSUER,
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")