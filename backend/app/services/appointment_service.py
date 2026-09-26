from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentCreate
from app.repositories.appointment_repository import AppointmentRepository


class AppointmentService:

    @staticmethod
    def create_appointment(
        db: Session,
        appointment: AppointmentCreate
    ):

        new_appointment = Appointment(
            **appointment.model_dump(),
            status="Scheduled"
        )

        return AppointmentRepository.create(
            db,
            new_appointment
        )