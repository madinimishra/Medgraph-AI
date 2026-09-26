from pydantic import BaseModel, EmailStr
from pydantic.config import ConfigDict


class DoctorCreate(BaseModel):
    doctor_code: str
    full_name: str
    specialization: str
    department_id: int
    qualification: str
    experience: int
    phone: str
    email: EmailStr


class DoctorResponse(BaseModel):
    id: int
    doctor_code: str
    full_name: str
    specialization: str
    department: str
    qualification: str
    experience: int
    phone: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)