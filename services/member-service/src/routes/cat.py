"""User cat profile routes"""
import json

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..database import get_db
from ..models import CreateCatRequest, UpdateCatRequest, UserCat

router = APIRouter(tags=["UserCat"])


def _row_to_cat(row) -> UserCat:
    tags = json.loads(row["personality_tags"]) if row["personality_tags"] else []
    return UserCat(
        userCatId=row["id"], name=row["name"], breed=row["breed"],
        age=row["age"], personalityTags=tags,
        vaccinationDate=row["vaccination_date"], photoUrl=row["photo_url"]
    )


@router.get("/members/me/cats")
def list_my_cats(user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM user_cats WHERE member_id=?", (user["memberId"],)).fetchall()
        return [_row_to_cat(r) for r in rows]
    finally:
        conn.close()


@router.post("/members/me/cats", status_code=201)
def create_cat(body: CreateCatRequest, user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO user_cats (member_id, name, breed, age, personality_tags, vaccination_date, photo_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user["memberId"], body.name, body.breed, body.age,
             json.dumps(body.personalityTags), body.vaccinationDate, body.photoUrl)
        )
        conn.commit()
        return {"message": "猫咪档案已创建"}
    finally:
        conn.close()


@router.put("/members/me/cats/{catId}")
def update_cat(catId: int, body: UpdateCatRequest, user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM user_cats WHERE id=? AND member_id=?", (catId, user["memberId"])
        ).fetchone()
        if not row:
            raise HTTPException(404, detail="猫咪档案不存在")
        updates = {}
        for field in ["name", "breed", "age", "vaccination_date", "photo_url"]:
            val = getattr(body, field, None)
            if val is not None and field != "vaccination_date":
                updates[field] = val
            elif val is not None and field == "vaccination_date":
                updates[field] = val
        if body.personalityTags is not None:
            updates["personality_tags"] = json.dumps(body.personalityTags)
        if updates:
            set_clause = ", ".join(f"{k}=?" for k in updates)
            conn.execute(f"UPDATE user_cats SET {set_clause} WHERE id=?", (*updates.values(), catId))
            conn.commit()
        return {"message": "更新成功"}
    finally:
        conn.close()


@router.delete("/members/me/cats/{catId}", status_code=204)
def delete_cat(catId: int, user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        conn.execute("DELETE FROM user_cats WHERE id=? AND member_id=?", (catId, user["memberId"]))
        conn.commit()
    finally:
        conn.close()
