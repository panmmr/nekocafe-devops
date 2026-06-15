"""
Reservation lifecycle management routes
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException

from ..database import get_db
from ..models import CreateReservationRequest, Reservation, ReservationStatus, RescheduleRequest

router = APIRouter(tags=["Reservation"])


@router.post("/reservations", status_code=201)
def create_reservation(body: CreateReservationRequest):
    conn = get_db()
    try:
        slot = conn.execute(
            "SELECT id, capacity FROM slots WHERE store_id=? AND slot_date=? AND time_slot=? AND slot_type!='cat-friendly' LIMIT 1",
            (body.storeId, body.date, body.timeSlot)
        ).fetchone()
        if not slot:
            raise HTTPException(409, detail="时段已满，无可预约桌位")

        existing = conn.execute(
            "SELECT COUNT(*) FROM reservations WHERE slot_id=? AND status NOT IN ('CANCELLED','COMPLETED')",
            (slot["id"],)
        ).fetchone()
        if existing[0] >= slot["capacity"]:
            raise HTTPException(409, detail="时段已满")

        cur = conn.execute(
            "INSERT INTO reservations (user_id,store_id,slot_id,resv_date,time_slot,guest_count,bring_cat,status,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (1, body.storeId, slot["id"], body.date, body.timeSlot, body.guestCount, int(body.bringCat), "CONFIRMED", datetime.utcnow().isoformat())
        )
        conn.commit()
        row = conn.execute("SELECT * FROM reservations WHERE id=?", (cur.lastrowid,)).fetchone()
        return _row_to_reservation(row)
    finally:
        conn.close()


@router.get("/reservations/{reservationId}")
def get_reservation(reservationId: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM reservations WHERE id=?", (reservationId,)).fetchone()
        if not row:
            raise HTTPException(404, detail="预约不存在")
        return _row_to_reservation(row)
    finally:
        conn.close()


@router.patch("/reservations/{reservationId}")
def reschedule(reservationId: int, body: RescheduleRequest):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM reservations WHERE id=?", (reservationId,)).fetchone()
        if not row:
            raise HTTPException(404, detail="预约不存在")
        new_date = body.newDate or row["resv_date"]
        new_slot = body.newTimeSlot or row["time_slot"]
        conn.execute(
            "UPDATE reservations SET resv_date=?, time_slot=? WHERE id=?",
            (new_date, new_slot, reservationId)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM reservations WHERE id=?", (reservationId,)).fetchone()
        return _row_to_reservation(row)
    finally:
        conn.close()


@router.post("/reservations/{reservationId}/cancel")
def cancel_reservation(reservationId: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM reservations WHERE id=?", (reservationId,)).fetchone()
        if not row:
            raise HTTPException(404, detail="预约不存在")
        created = datetime.fromisoformat(row["created_at"])
        if datetime.utcnow() - created < timedelta(hours=2):
            raise HTTPException(400, detail="距预约时间不足2小时，不可免费取消")
        buffer_expires = (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        conn.execute(
            "UPDATE reservations SET status='CANCELLED', buffer_expires_at=? WHERE id=?",
            (buffer_expires, reservationId)
        )
        conn.commit()
        return {"message": "取消成功，桌位进入缓冲池（5分钟）", "bufferExpiresAt": buffer_expires}
    finally:
        conn.close()


@router.post("/reservations/{reservationId}/arrive")
def arrive(reservationId: int):
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM reservations WHERE id=?", (reservationId,)).fetchone()
        if not row:
            raise HTTPException(404, detail="预约不存在")
        conn.execute("UPDATE reservations SET status='ARRIVED' WHERE id=?", (reservationId,))
        conn.commit()
        return {"message": "到店确认成功"}
    finally:
        conn.close()


def _row_to_reservation(row) -> dict:
    return {
        "reservationId": row["id"],
        "userId": row["user_id"],
        "storeId": row["store_id"],
        "slotId": row["slot_id"],
        "date": row["resv_date"],
        "timeSlot": row["time_slot"],
        "guestCount": row["guest_count"],
        "bringCat": bool(row["bring_cat"]),
        "status": row["status"],
        "bufferExpiresAt": row["buffer_expires_at"],
        "createdAt": row["created_at"],
    }
