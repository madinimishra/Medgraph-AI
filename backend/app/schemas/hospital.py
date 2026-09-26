from pydantic import BaseModel


class HospitalCreate(BaseModel):
    hospital_code: str
    hospital_name: str
    address: str
    city: str
    state: str
    country: str


class HospitalResponse(HospitalCreate):
    id: int

    class Config:
        from_attributes = True