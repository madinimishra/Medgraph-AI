from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db

from app.schemas.hospital import (
    HospitalCreate,
    HospitalResponse
)

from app.services.hospital_service import HospitalService
from app.repositories.hospital_repository import HospitalRepository

from app.core.rbac import require_roles

router = APIRouter(
    prefix="/hospitals",
    tags=["Hospitals"]
)


@router.post(
    "/",
    response_model=HospitalResponse
)
def create_hospital(
    hospital: HospitalCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin"))
):
    try:
        return HospitalService.create_hospital(
            db,
            hospital
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=list[HospitalResponse]
)
def get_hospitals(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin"))
):
    return HospitalRepository.get_all(db)