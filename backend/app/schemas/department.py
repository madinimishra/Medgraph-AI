from pydantic import BaseModel
from pydantic.config import ConfigDict


class DepartmentCreate(BaseModel):

    department_code: str
    department_name: str
    description: str | None = None
    floor: str
    hod_name: str


class DepartmentResponse(DepartmentCreate):

    id: int

    model_config = ConfigDict(from_attributes=True)