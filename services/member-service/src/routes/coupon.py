"""Coupon routes"""

from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..database import get_db
from ..models import Coupon

router = APIRouter(tags=["Coupon"])


@router.get("/members/me/coupons")
def get_my_coupons(user: dict = Depends(get_current_user)):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT id, type, discount_value, valid_from, valid_until, used FROM coupons WHERE member_id=? ORDER BY valid_until DESC",
            (user["memberId"],),
        ).fetchall()
        # seed if empty
        if not rows:
            conn.execute(
                "INSERT INTO coupons (member_id, type, discount_value, valid_from, valid_until) VALUES (?, ?, ?, ?, ?)",
                (user["memberId"], "discount", 20.0, "2026-06-01", "2026-12-31"),
            )
            conn.execute(
                "INSERT INTO coupons (member_id, type, discount_value, valid_from, valid_until) VALUES (?, ?, ?, ?, ?)",
                (user["memberId"], "meal_voucher", 50.0, "2026-06-01", "2026-09-30"),
            )
            conn.commit()
            rows = conn.execute(
                "SELECT id, type, discount_value, valid_from, valid_until, used FROM coupons WHERE member_id=? ORDER BY valid_until DESC",
                (user["memberId"],),
            ).fetchall()
        return [
            Coupon(
                couponId=r["id"],
                type=r["type"],
                discountValue=r["discount_value"],
                validFrom=r["valid_from"],
                validUntil=r["valid_until"],
                used=bool(r["used"]),
            )
            for r in rows
        ]
    finally:
        conn.close()
