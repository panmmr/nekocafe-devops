"""Pydantic models for Member Service"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class MemberLevel(str, Enum):
    NORMAL = "NORMAL"
    SILVER = "SILVER"
    GOLD = "GOLD"
    DIAMOND = "DIAMOND"


class Member(BaseModel):
    memberId: int
    phone: str
    nickname: str
    level: MemberLevel
    points: int
    totalSpending: float
    createdAt: datetime


class RegisterRequest(BaseModel):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    smsCode: str
    nickname: Optional[str] = None


class LoginRequest(BaseModel):
    phone: Optional[str] = None
    smsCode: Optional[str] = None
    wechatCode: Optional[str] = None


class AuthResponse(BaseModel):
    accessToken: str
    refreshToken: str
    expiresIn: int = 3600
    tokenType: str = "Bearer"


class RefreshRequest(BaseModel):
    refreshToken: str


class MemberUpdate(BaseModel):
    nickname: Optional[str] = None


class LevelInfo(BaseModel):
    currentLevel: MemberLevel
    totalSpending: float
    nextLevel: MemberLevel
    amountToNextLevel: float


class PointsInfo(BaseModel):
    balance: int
    recentTransactions: list[dict]


class ExchangeRequest(BaseModel):
    rewardId: int


class UserCat(BaseModel):
    userCatId: int
    name: str
    breed: str
    age: Optional[int] = None
    personalityTags: list[str] = []
    vaccinationDate: Optional[str] = None
    photoUrl: Optional[str] = None


class CreateCatRequest(BaseModel):
    name: str
    breed: str
    age: Optional[int] = None
    personalityTags: list[str] = []
    vaccinationDate: Optional[str] = None
    photoUrl: Optional[str] = None


class UpdateCatRequest(BaseModel):
    name: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None
    personalityTags: Optional[list[str]] = None
    vaccinationDate: Optional[str] = None
    photoUrl: Optional[str] = None


class Coupon(BaseModel):
    couponId: int
    type: str
    discountValue: float
    validFrom: date
    validUntil: date
    used: bool
