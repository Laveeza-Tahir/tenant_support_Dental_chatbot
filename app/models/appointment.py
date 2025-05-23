from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import settings
from datetime import datetime
from typing import Optional

client = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db]
appointments = db.appointments

class Appointment:
    def __init__(
        self,
        session_id: str,
        patient_name: str,
        appointment_time: datetime,
        appointment_type: str,
        status: str = "scheduled",
        reminder_sent: bool = False
    ):
        self.session_id = session_id
        self.patient_name = patient_name
        self.appointment_time = appointment_time
        self.appointment_type = appointment_type
        self.status = status
        self.reminder_sent = reminder_sent
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    async def save(self):
        await appointments.update_one(
            {"session_id": self.session_id},
            {
                "$set": {
                    "patient_name": self.patient_name,
                    "appointment_time": self.appointment_time,
                    "appointment_type": self.appointment_type,
                    "status": self.status,
                    "reminder_sent": self.reminder_sent,
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "session_id": self.session_id,
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