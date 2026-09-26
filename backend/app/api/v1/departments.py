from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db

from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse
)

from app.services.department_service import DepartmentService
from app.repositories.department_repository import DepartmentRepository

from app.core.rbac import require_roles

router = APIRouter(
    prefix="/departments",
    tags=["Departments"]
)


@router.post(
    "/",
    response_model=DepartmentResponse
)
def create_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin"))
):
    try:
        return DepartmentService.create_department(
            db,
            department
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=list[DepartmentResponse]
)
def get_departments(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles("admin", "doctor")
    )
):
    return DepartmentRepository.get_all(db)