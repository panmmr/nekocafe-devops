"""
Pydantic models matching OpenAPI 3.0 schemas for Reservation Service
"""
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReservationStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    ARRIVED = "ARRIVED"
    NO_SHOW = "NO_SHOW"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class QueueStatus(str, Enum):
    WAITING = "WAITING"
    NOTIFIED = "NOTIFIED"
    CONFIRMED = "CONFIRMED"
    EXPIRED = "EXPIRED"


class SlotType(BaseModel):
    type: str = Field(example="cat-friendly")
    capacity: int
    available: int


class TimeSlotAvailability(BaseModel):
    timeSlot: str = Field(example="18:00-20:00")
    totalSlots: int
    availableSlots: int
    slotTypes: list[SlotType]


class AvailabilityResponse(BaseModel):
    storeId: int
    date: str
    timeSlots: list[TimeSlotAvailability]


class PreOrderItem(BaseModel):
    menuItemId: int
    quantity: int
    specialNotes: Optional[str] = None


class CreateReservationRequest(BaseModel):
    storeId: int
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    timeSlot: str
    guestCount: int = Field(ge=1, le=10)
    bringCat: bool = False
    catId: Optional[int] = None
    enableMatching: bool = False
    preOrderItems: list[PreOrderItem] = []


class Reservation(BaseModel):
    reservationId: int
    userId: int
    storeId: int
    slotId: int
    date: str
    timeSlot: str
    guestCount: int
    bringCat: bool
    status: ReservationStatus
    bufferExpiresAt: Optional[datetime] = None
    createdAt: datetime


class RescheduleRequest(BaseModel):
    newDate: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    newTimeSlot: Optional[str] = None


class CatMatchingRequest(BaseModel):
    storeId: int
    userId: int
    userCatId: int


class CatMatchingRecommendation(BaseModel):
    slotId: int
    tableNumber: str
    matchScore: float
    reasons: list[str]


class CatMatchingResponse(BaseModel):
    recommendations: list[CatMatchingRecommendation]


class QueueTicket(BaseModel):
    ticketId: int
    storeId: int
    queueNumber: int
    estimatedWaitMinutes: int
    aheadCount: int
    status: QueueStatus


class ErrorResponse(BaseModel):
    errorCode: str = Field(example="40101")
    message: str
    timestamp: datetime
