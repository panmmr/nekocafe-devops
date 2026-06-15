"""
Queuing / take-a-number routes
"""

import random

from fastapi import APIRouter, HTTPException

from ..database import get_db
from ..models import QueueTicket

router = APIRouter(tags=["Queue"])


@router.post("/stores/{storeId}/queue", status_code=201)
def join_queue(storeId: int):
    conn = get_db()
    try:
        max_num = conn.execute(
            "SELECT COALESCE(MAX(queue_number),0) FROM queue_tickets WHERE store_id=? AND status='WAITING'",
            (storeId,),
        ).fetchone()[0]
        ahead = conn.execute(
            "SELECT COUNT(*) FROM queue_tickets WHERE store_id=? AND status='WAITING'",
            (storeId,),
        ).fetchone()[0]
        wait = max(5, ahead * 10 + random.randint(0, 10))
        cur = conn.execute(
            "INSERT INTO queue_tickets (store_id,queue_number,estimated_wait_minutes,ahead_count,status) VALUES (?,?,?,?,?)",
            (storeId, max_num + 1, wait, ahead, "WAITING"),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM queue_tickets WHERE id=?", (cur.lastrowid,)
        ).fetchone()
        return QueueTicket(
            ticketId=row["id"],
            storeId=row["store_id"],
            queueNumber=row["queue_number"],
            estimatedWaitMinutes=row["estimated_wait_minutes"],
            aheadCount=row["ahead_count"],
            status=row["status"],
        )
    finally:
        conn.close()


@router.get("/queue/{ticketId}")
def get_queue_progress(ticketId: int):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM queue_tickets WHERE id=?", (ticketId,)
        ).fetchone()
        if not row:
            raise HTTPException(404, detail="排队号不存在")
        ahead = conn.execute(
            "SELECT COUNT(*) FROM queue_tickets WHERE store_id=? AND status='WAITING' AND queue_number < ?",
            (row["store_id"], row["queue_number"]),
        ).fetchone()[0]
        conn.execute(
            "UPDATE queue_tickets SET ahead_count=? WHERE id=?", (ahead, ticketId)
        )
        conn.commit()
        return {
            "ticketId": row["id"],
            "queueNumber": row["queue_number"],
            "estimatedWaitMinutes": max(5, ahead * 10),
            "aheadCount": ahead,
            "status": row["status"],
        }
    finally:
        conn.close()


@router.delete("/queue/{ticketId}", status_code=204)
def cancel_queue(ticketId: int):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE queue_tickets SET status='EXPIRED' WHERE id=?", (ticketId,)
        )
        conn.commit()
    finally:
        conn.close()
