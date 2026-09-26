from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db

from app.schemas.medical_record import (
    MedicalRecordCreate,
    MedicalRecordResponse
)

from app.services.medical_record_service import (
    MedicalRecordService
)

from app.repositories.medical_record_repository import (
    MedicalRecordRepository
)

from app.core.rbac import require_roles

router = APIRouter(
    prefix="/medical-records",
    tags=["Medical Records"]
)


@router.post(
    "/",
    response_model=MedicalRecordResponse
)
def create_record(
    record: MedicalRecordCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "doctor"
        )
    )
):
    try:
        return MedicalRecordService.create_record(
            db,
            record
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=list[MedicalRecordResponse]
)
def get_all_records(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "admin",
            "doctor"
        )
    )
):
    return MedicalRecordRepository.get_all(db)


@router.get(
    "/patient/{patient_id}",
    response_model=list[MedicalRecordResponse]
)
def get_patient_history(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "doctor",
            "admin"
        )
    )
):
    return MedicalRecordRepository.get_by_patient(
        db,
        patient_id
    )