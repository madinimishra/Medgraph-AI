from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.patient import PatientCreate, PatientResponse
from app.services.patient_service import PatientService
from app.repositories.patient_repository import PatientRepository

from app.core.rbac import require_roles

router = APIRouter(
    prefix="/patients",
    tags=["Patients"]
)


# -------------------------
# Create Patient
# -------------------------
@router.post(
    "/",
    response_model=PatientResponse
)
def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "admin",
            "doctor",
            "receptionist"
        )
    )
):
    try:
        return PatientService.create_patient(
            db,
            patient
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# -------------------------
# Get All Patients
# -------------------------
@router.get(
    "/",
    response_model=list[PatientResponse]
)
def get_all_patients(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "admin",
            "doctor",
            "receptionist"
        )
    )
):
    return PatientRepository.get_all(db)


# -------------------------
# Get Patient By ID
# -------------------------
@router.get(
    "/{patient_id}",
    response_model=PatientResponse
)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "admin",
            "doctor",
            "receptionist"
        )
    )
):
    patient = PatientRepository.get_by_id(
        db,
        patient_id
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    return patient