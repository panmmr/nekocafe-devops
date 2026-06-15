"""Member profile routes"""
from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..database import get_db
from ..models import LevelInfo, Member, MemberLevel, MemberUpdate

router = APIRouter(tags=["Member"])

LEVEL_THRESHOLDS = [
    (MemberLevel.NORMAL, 0),
    (MemberLevel.SILVER, 1000),
    (MemberLevel.GOLD, 5000),
    (MemberLevel.DIAMOND, 20000),
]


def _calc_level(spending: float) -> tuple[MemberLevel, MemberLevel, float]:
    current = MemberLevel.NORMAL
    next_level = MemberLevel.SILVER
    for i, (lv, threshold) in enumerate(LEVEL_THRESHOLDS):
        if spending >= threshold:
            current = lv
            if i + 1 < len(LEVEL_THRESHOLDS):
                next_level = LEVEL_THRESHOLDS[i + 1][0]
            else:
                next_level = lv
    amount_next = max(0, LEVEL_THRESHOLDS[
        [i for i, (_, t) in enumerate(LEVEL_THRESHOLDS) if LEVEL_THRESHOLDS[i][0] == next_level][0]
    ][1] - spending)
    return current, next_level, amount_next


@router.get("/members/me")
def get_my_profile(user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM members WHERE id=?", (user["memberId"],)).fetchone()
        if not row:
            return {}
        current_lv, _, _ = _calc_level(row["total_spending"])
        return Member(
            memberId=row["id"],
            phone=row["phone"],
            nickname=row["nickname"],
            level=current_lv,
            points=row["points"],
            totalSpending=row["total_spending"],
            createdAt=row["created_at"],
        )
    finally:
        conn.close()


@router.patch("/members/me")
def update_profile(body: MemberUpdate, user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        if body.nickname is not None:
            conn.execute("UPDATE members SET nickname=? WHERE id=?", (body.nickname, user["memberId"]))
            conn.commit()
        return {"message": "更新成功"}
    finally:
        conn.close()


@router.get("/members/me/level")
def get_my_level(user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        row = conn.execute("SELECT total_spending FROM members WHERE id=?", (user["memberId"],)).fetchone()
        if not row:
            return {}
        spending = row["total_spending"]
        current, nxt, amount = _calc_level(spending)
        return LevelInfo(currentLevel=current, totalSpending=spending, nextLevel=nxt, amountToNextLevel=amount)
    finally:
        conn.close()
