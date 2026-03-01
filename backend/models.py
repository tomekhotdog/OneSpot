from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def new_id() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.utcnow()


class AvailabilityPermission(str, Enum):
    ANYONE = "anyone"
    OWNERS_ONLY = "owners_only"


class User(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str
    flat_number: str
    phone: str
    is_owner: bool = False
    bay_number: Optional[str] = None
    availability_permission: AvailabilityPermission = AvailabilityPermission.ANYONE
    credits: int = 24
    created_at: datetime = Field(default_factory=now_utc)
    last_login: datetime = Field(default_factory=now_utc)


class Session(BaseModel):
    user_id: str
    created_at: datetime = Field(default_factory=now_utc)
    expires_at: datetime


class OTPRequest(BaseModel):
    code: str
    created_at: datetime = Field(default_factory=now_utc)
    expires_at: datetime
    attempts: int = 0
    request_count_window: int = 1
    window_start: datetime = Field(default_factory=now_utc)


class DayHours(BaseModel):
    start: int  # 0-23
    end: int  # 1-24 (end > start)


class AvailabilityType(str, Enum):
    RECURRING = "recurring"
    ONE_OFF = "one_off"


class Availability(BaseModel):
    id: str = Field(default_factory=new_id)
    user_id: str
    bay_number: str
    type: AvailabilityType
    # Recurring fields
    pattern: Optional[dict[str, Optional[DayHours]]] = None
    exclusions: list[str] = Field(default_factory=list)
    # One-off fields
    date: Optional[str] = None
    start_hour: Optional[int] = None
    end_hour: Optional[int] = None
    # Common
    created_at: datetime = Field(default_factory=now_utc)
    paused: bool = False


class BookingStatus(str, Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Booking(BaseModel):
    id: str = Field(default_factory=new_id)
    booker_user_id: str
    owner_user_id: str
    bay_number: str
    date: str
    start_hour: int
    end_hour: int
    credits_charged: int
    status: BookingStatus = BookingStatus.CONFIRMED
    created_at: datetime = Field(default_factory=now_utc)
    modified_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    reminder_sent: bool = False


class CreditType(str, Enum):
    INITIAL_GRANT = "initial_grant"
    BOOKING_CHARGE = "booking_charge"
    BOOKING_EARNING = "booking_earning"
    CANCELLATION_REFUND = "cancellation_refund"
    CANCELLATION_DEBIT = "cancellation_debit"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class CreditLedgerEntry(BaseModel):
    id: str = Field(default_factory=new_id)
    user_id: str
    amount: int
    type: CreditType
    related_booking_id: Optional[str] = None
    description: str
    timestamp: datetime = Field(default_factory=now_utc)


class WhatsAppLogEntry(BaseModel):
    id: str = Field(default_factory=new_id)
    recipient: str
    template: str
    params: dict = Field(default_factory=dict)
    status: str = "sent"
    timestamp: datetime = Field(default_factory=now_utc)


class AppState(BaseModel):
    users: dict[str, User] = Field(default_factory=dict)
    sessions: dict[str, Session] = Field(default_factory=dict)
    otp_requests: dict[str, OTPRequest] = Field(default_factory=dict)
    availability: dict[str, Availability] = Field(default_factory=dict)
    bookings: dict[str, Booking] = Field(default_factory=dict)
    credit_ledger: list[CreditLedgerEntry] = Field(default_factory=list)
    whatsapp_log: list[WhatsAppLogEntry] = Field(default_factory=list)
