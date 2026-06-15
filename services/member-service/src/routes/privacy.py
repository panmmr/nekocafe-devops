"""Privacy compliance routes (data export / deletion)"""

from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..database import get_db

router = APIRouter(tags=["Privacy"])


@router.post("/members/me/data/export", status_code=202)
def export_my_data(user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        member = conn.execute(
            "SELECT * FROM members WHERE id=?", (user["memberId"],)
        ).fetchone()
        cats = conn.execute(
            "SELECT * FROM user_cats WHERE member_id=?", (user["memberId"],)
        ).fetchall()
        data = {
            "memberId": member["id"],
            "phone": member["phone"],
            "nickname": member["nickname"],
            "cats": [dict(c) for c in cats],
            "requestedAt": "2026-06-15T00:00:00Z",
        }
        return {
            "message": "数据导出请求已接受",
            "estimatedReadyHours": 24,
            "data": data,
        }
    finally:
        conn.close()


@router.post("/members/me/data/delete", status_code=202)
def delete_my_data(user: dict = Depends(get_current_user)):
    return {"message": "删除请求已接受，30天内完成处理"}
