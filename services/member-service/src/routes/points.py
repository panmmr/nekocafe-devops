"""Points and exchange routes"""

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..database import get_db
from ..models import ExchangeRequest, PointsInfo

router = APIRouter(tags=["Points"])


@router.get("/members/me/points")
def get_my_points(user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT points FROM members WHERE id=?", (user["memberId"],)
        ).fetchone()
        txs = conn.execute(
            "SELECT amount, description, created_at FROM points_transactions WHERE member_id=? ORDER BY created_at DESC LIMIT 10",
            (user["memberId"],),
        ).fetchall()
        recent = [
            {
                "amount": t["amount"],
                "description": t["description"],
                "createdAt": t["created_at"],
            }
            for t in txs
        ]
        return PointsInfo(
            balance=row["points"] if row else 0, recentTransactions=recent
        )
    finally:
        conn.close()


@router.post("/members/me/points/exchange")
def exchange_points(body: ExchangeRequest, user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT points FROM members WHERE id=?", (user["memberId"],)
        ).fetchone()
        if not row or row["points"] < 100:
            raise HTTPException(400, detail="积分不足")
        conn.execute(
            "UPDATE members SET points=points-100 WHERE id=?", (user["memberId"],)
        )
        conn.execute(
            "INSERT INTO points_transactions (member_id, amount, description) VALUES (?, ?, ?)",
            (user["memberId"], -100, f"兑换奖励 #{body.rewardId}"),
        )
        conn.commit()
        return {"message": "兑换成功", "pointsDeducted": 100}
    finally:
        conn.close()
