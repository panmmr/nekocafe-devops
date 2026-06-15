"""Authentication routes: register, login, refresh"""

from fastapi import APIRouter, HTTPException

from ..auth import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from ..database import get_db
from ..models import AuthResponse, LoginRequest, RefreshRequest, RegisterRequest

router = APIRouter(tags=["Auth"])


@router.post("/auth/register", status_code=201)
def register(body: RegisterRequest):
    conn = get_db()
    try:
        existing = conn.execute(
            "SELECT id FROM members WHERE phone=?", (body.phone,)
        ).fetchone()
        if existing:
            raise HTTPException(409, detail="手机号已注册")
        nickname = body.nickname or f"猫友{body.phone[-4:]}"
        conn.execute(
            "INSERT INTO members (phone, nickname) VALUES (?, ?)",
            (body.phone, nickname),
        )
        conn.commit()
        member = conn.execute(
            "SELECT id, phone FROM members WHERE phone=?", (body.phone,)
        ).fetchone()
        access = create_access_token(member["id"], member["phone"])
        refresh = create_refresh_token(member["id"])
        return AuthResponse(accessToken=access, refreshToken=refresh)
    finally:
        conn.close()


@router.post("/auth/login")
def login(body: LoginRequest):
    conn = get_db()
    try:
        if body.phone:
            member = conn.execute(
                "SELECT id, phone FROM members WHERE phone=?", (body.phone,)
            ).fetchone()
        elif body.wechatCode:
            member = conn.execute(
                "SELECT id, phone FROM members WHERE phone=?", ("13800138000",)
            ).fetchone()
        else:
            raise HTTPException(400, detail="请提供手机号或微信授权码")
        if not member:
            raise HTTPException(401, detail="用户不存在")
        access = create_access_token(member["id"], member["phone"])
        refresh = create_refresh_token(member["id"])
        return AuthResponse(accessToken=access, refreshToken=refresh)
    finally:
        conn.close()


@router.post("/auth/refresh")
def refresh_token(body: RefreshRequest):
    member_id = verify_refresh_token(body.refreshToken)
    if not member_id:
        raise HTTPException(401, detail="refresh token 无效或已过期")
    conn = get_db()
    try:
        member = conn.execute(
            "SELECT phone FROM members WHERE id=?", (member_id,)
        ).fetchone()
        if not member:
            raise HTTPException(401, detail="用户不存在")
        access = create_access_token(member_id, member["phone"])
        refresh = create_refresh_token(member_id)
        return AuthResponse(accessToken=access, refreshToken=refresh)
    finally:
        conn.close()
