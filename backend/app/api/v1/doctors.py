from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.doctor import DoctorCreate, DoctorResponse
from app.repositories.doctor_repository import DoctorRepository
from app.services.doctor_service import DoctorService
from app.core.rbac import require_roles

router = APIRouter(
    prefix="/doctors",
    tags=["Doctors"]
)


@router.post(
    "/",
    response_model=DoctorResponse
)
def create_doctor(
    doctor: DoctorCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin"))
):
    try:
        return DoctorService.create_doctor(
            db,
            doctor
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=list[DoctorResponse]
)
def get_all_doctors(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "doctor"))
):
    return DoctorRepository.get_all(db)


@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse
)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "doctor"))
):
    doctor = DoctorRepository.get_by_id(db, doctor_id)

    if doctor is None:
        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    return doctor