import base64
import hashlib
import hmac
import json
import secrets
import time
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"
def verify_password(password: str, encoded: str) -> bool:
    try:
        _, salt, digest = encoded.split("$")
        value = hashlib.scrypt(password.encode(), salt=base64.urlsafe_b64decode(salt), n=2**14, r=8, p=1)
        return hmac.compare_digest(base64.urlsafe_b64encode(value).decode(), digest)
    except (ValueError, TypeError):
        return False
def _encode(data: dict[str, object], secret: str) -> str:
    def part(value: bytes) -> str: return base64.urlsafe_b64encode(value).rstrip(b"=").decode()
    header = part(b'{"alg":"HS256","typ":"JWT"}')
    payload = part(json.dumps(data, separators=(",", ":")).encode())
    signature = part(hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"
def create_token(user_id: UUID, secret: str, expires_minutes: int) -> str:
    return _encode({"sub": str(user_id), "exp": int(time.time()) + expires_minutes * 60}, secret)
def decode_token(token: str, secret: str) -> UUID | None:
    try:
        header, payload, signature = token.split(".")
        expected = base64.urlsafe_b64encode(hmac.new(secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if int(data["exp"]) < int(time.time()):
            return None
        return UUID(str(data["sub"]))
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None

class AuthService:
    def __init__(self, session: Session) -> None: self.session = session
    def register(self, email: str, password: str) -> User:
        user = User(email=email.lower(), password_hash=hash_password(password))
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    def authenticate(self, email: str, password: str) -> User | None:
        user = self.session.scalar(select(User).where(User.email == email.lower()))
        return user if user and user.is_active and verify_password(password, user.password_hash) else None
