from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Literal, Optional

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: Literal["admin", "doctor", "receptionist"]
    provider_id: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    provider_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


class UpdateProviderLink(BaseModel):
    provider_id: Optional[str] = None  # None/omitted unlinks the user


class UpdateUserRole(BaseModel):
    role: Literal["admin", "doctor", "receptionist"]
