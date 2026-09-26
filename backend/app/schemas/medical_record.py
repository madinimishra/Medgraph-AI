from datetime import date
from pydantic import BaseModel


class MedicalRecordCreate(BaseModel):

    patient_id: int

    doctor_id: int

    appointment_id: int

    diagnosis: str

    symptoms: str | None = None

    prescription: str | None = None

    lab_tests: str | None = None

    notes: str | None = None

    follow_up_date: date | None = None


class MedicalRecordResponse(MedicalRecordCreate):

    id: int

    class Config:
        from_attributes = True