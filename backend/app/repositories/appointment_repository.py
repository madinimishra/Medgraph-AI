from sqlalchemy.orm import Session

from app.models.appointment import Appointment


class AppointmentRepository:

    @staticmethod
    def create(db: Session, appointment: Appointment):
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def get_all(db: Session):
        return db.query(Appointment).all()