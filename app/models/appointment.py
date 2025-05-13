from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, validator

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db]
appointments = db.appointments

class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"

class AppointmentModel(BaseModel):
    """Pydantic model for appointment data validation"""
    tenant_id: str
    calendar_id: Optional[str] = None
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: int = 30
    appointment_type: str
    notes: Optional[str] = None
    status: AppointmentStatus = AppointmentStatus.PENDING
    
    @validator('end_time', pre=True, always=True)
    def set_end_time(cls, v, values):
        """Calculate end time if not provided"""
        if v is None and 'start_time' in values and 'duration_minutes' in values:
            from datetime import timedelta
            return values['start_time'] + timedelta(minutes=values['duration_minutes'])
        return v

class Appointment:
    def __init__(
        self,
        session_id: str,
        patient_name: str,
        appointment_time: datetime,
        appointment_type: str,
        tenant_id: str,
        status: str = "scheduled",
        reminder_sent: bool = False,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        calendar_id: Optional[str] = None,
        notes: Optional[str] = None,
        customer_data: Optional[Dict[str, Any]] = None
    ):
        self.session_id = session_id
        self.tenant_id = tenant_id  # Added tenant_id for multi-tenant support
        self.patient_name = patient_name
        self.appointment_time = appointment_time
        self.appointment_type = appointment_type
        self.status = status
        self.reminder_sent = reminder_sent
        self.customer_email = customer_email
        self.customer_phone = customer_phone
        self.calendar_id = calendar_id
        self.notes = notes
        self.customer_data = customer_data or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    async def save(self):
        await appointments.update_one(
            {"session_id": self.session_id, "tenant_id": self.tenant_id},
            {
                "$set": {
                    "patient_name": self.patient_name,
                    "appointment_time": self.appointment_time,
                    "appointment_type": self.appointment_type,
                    "status": self.status,
                    "reminder_sent": self.reminder_sent,
                    "customer_email": self.customer_email,
                    "customer_phone": self.customer_phone,
                    "calendar_id": self.calendar_id,
                    "notes": self.notes,
                    "customer_data": self.customer_data,
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "session_id": self.session_id,
                    "tenant_id": self.tenant_id,
                    "created_at": self.created_at
                }
            },
            upsert=True
        )

    @staticmethod
    async def get_by_session(session_id: str):
        return await appointments.find_one({"session_id": session_id})

    @staticmethod
    async def update_status(session_id: str, status: str):
        await appointments.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.utcnow()
                }
            }
        )

    @staticmethod
    async def mark_reminder_sent(session_id: str):
        await appointments.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "reminder_sent": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )