"""
JWT authentication utilities
"""
import os
import secrets
import time
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_hex(32))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = 3600
REFRESH_TOKEN_EXPIRE = 86400 * 7

security = HTTPBearer(auto_error=False)


def create_access_token(member_id: int, phone: str) -> str:
    payload = {
        "sub": str(member_id),
        "phone": phone,
        "iat": int(time.time()),
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE,
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(member_id: int) -> str:
    token = secrets.token_urlsafe(48)
    from .database import get_db
    conn = get_db()
    try:
        expires = (datetime.utcnow() + timedelta(seconds=REFRESH_TOKEN_EXPIRE)).isoformat()
        conn.execute(
            "INSERT INTO refresh_tokens (member_id, token, expires_at) VALUES (?, ?, ?)",
            (member_id, token, expires)
        )
        conn.commit()
    finally:
        conn.close()
    return token


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(401, detail="无效的 token 类型")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, detail="token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(401, detail="无效的 token")


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict:
    if not credentials:
        raise HTTPException(401, detail="缺少认证信息")
    payload = decode_access_token(credentials.credentials)
    return {"memberId": int(payload["sub"]), "phone": payload["phone"]}


def verify_refresh_token(token: str) -> int | None:
    from .database import get_db
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT member_id, expires_at, revoked FROM refresh_tokens WHERE token=?",
            (token,)
        ).fetchone()
        if not row or row["revoked"]:
            return None
        if datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
            return None
        return row["member_id"]
    finally:
        conn.close()
