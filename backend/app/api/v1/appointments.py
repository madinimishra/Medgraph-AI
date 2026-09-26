from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db

from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse
)

from app.services.appointment_service import AppointmentService
from app.repositories.appointment_repository import AppointmentRepository

from app.core.rbac import require_roles

router = APIRouter(
    prefix="/appointments",
    tags=["Appointments"]
)


@router.post(
    "/",
    response_model=AppointmentResponse
)
def create_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "admin",
            "receptionist"
        )
    )
):
    return AppointmentService.create_appointment(
        db,
        appointment
    )


@router.get(
    "/",
    response_model=list[AppointmentResponse]
)
def get_all_appointments(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_roles(
            "admin",
            "doctor",
            "receptionist"
        )
    )
):
    return AppointmentRepository.get_all(db)