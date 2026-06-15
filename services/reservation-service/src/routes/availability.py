"""
Store table availability routes
"""
from fastapi import APIRouter, Query

from ..database import get_db
from ..models import AvailabilityResponse, SlotType, TimeSlotAvailability

router = APIRouter(tags=["Availability"])


@router.get("/stores/{storeId}/availability")
def get_availability(
    storeId: int,
    date: str = Query(...),
    guestCount: int = Query(1, ge=1),
    bringCat: bool = Query(False),
):
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT time_slot, slot_type, capacity, table_number FROM slots WHERE store_id=? AND slot_date=? ORDER BY time_slot",
            (storeId, date)
        ).fetchall()
        if not rows:
            time_slots = []
        else:
            grouped = {}
            for r in rows:
                ts = r["time_slot"]
                if ts not in grouped:
                    grouped[ts] = {"total": 0, "available": 0, "types": []}
                reserved = conn.execute(
                    "SELECT COUNT(*) FROM reservations WHERE slot_id IN (SELECT id FROM slots WHERE store_id=? AND slot_date=? AND time_slot=?) AND status NOT IN ('CANCELLED','COMPLETED')",
                    (storeId, date, ts)
                ).fetchone()[0]
                cap = r["capacity"]
                grouped[ts]["total"] += cap
                grouped[ts]["available"] += max(0, cap - reserved)
                grouped[ts]["types"].append({
                    "type": r["slot_type"],
                    "capacity": cap,
                    "available": max(0, cap - reserved)
                })
            time_slots = [
                TimeSlotAvailability(
                    timeSlot=ts,
                    totalSlots=v["total"],
                    availableSlots=v["available"],
                    slotTypes=[SlotType(**t) for t in v["types"]]
                )
                for ts, v in grouped.items()
            ]
        return AvailabilityResponse(storeId=storeId, date=date, timeSlots=time_slots)
    finally:
        conn.close()
