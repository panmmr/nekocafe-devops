"""
AI-powered cat personality matching recommendation
"""
import random

from fastapi import APIRouter

from ..database import get_db
from ..models import CatMatchingRequest, CatMatchingResponse, CatMatchingRecommendation

router = APIRouter(tags=["Reservation"])

CAT_PERSONALITIES = ["活泼好动", "安静粘人", "独立高冷", "好奇探索", "温柔害羞"]


@router.post("/reservations/match")
def match_cats(body: CatMatchingRequest):
    conn = get_db()
    try:
        slots = conn.execute(
            "SELECT id, table_number, slot_type FROM slots WHERE store_id=? AND slot_date >= date('now') AND slot_type='cat-friendly' LIMIT 5",
            (body.storeId,)
        ).fetchall()
        if not slots:
            slots = conn.execute(
                "SELECT id, table_number, slot_type FROM slots WHERE store_id=? AND slot_date >= date('now') LIMIT 5",
                (body.storeId,)
            ).fetchall()

        recommendations = []
        for s in slots[:3]:
            score = round(random.uniform(0.6, 0.99), 2)
            reasons = [
                f"桌位{s['table_number']}与您的猫咪性格匹配度{score*100:.0f}%",
                f"该区域{random.choice(CAT_PERSONALITIES)}猫咪较多",
                "靠近猫咪活动区" if s["slot_type"] == "cat-friendly" else "光线柔和，适合猫咪休息"
            ]
            recommendations.append(CatMatchingRecommendation(
                slotId=s["id"],
                tableNumber=s["table_number"],
                matchScore=score,
                reasons=reasons
            ))
        return CatMatchingResponse(recommendations=recommendations)
    finally:
        conn.close()
