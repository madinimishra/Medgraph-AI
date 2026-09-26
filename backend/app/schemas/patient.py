from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr


class PatientBase(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    gender: str
    date_of_birth: date
    phone: str
    alternate_phone: Optional[str] = None
    email: EmailStr
    blood_group: Optional[str] = None
    address: str
    city: str
    state: str
    country: str
    postal_code: str
    emergency_contact_name: str
    emergency_contact_phone: str
    emergency_contact_relation: str


class PatientCreate(PatientBase):
    pass


class PatientUpdate(PatientBase):
    pass


class PatientResponse(PatientBase):
    id: int
    patient_code: str
    is_active: bool

    class Config:
        from_attributes = True