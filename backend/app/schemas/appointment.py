from datetime import date, time
from pydantic import BaseModel


class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: date
    appointment_time: time
    reason: str


class AppointmentResponse(AppointmentCreate):
    id: int
    status: str

    class Config:
        from_attributes = True