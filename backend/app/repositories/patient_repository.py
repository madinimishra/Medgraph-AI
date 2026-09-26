from sqlalchemy.orm import Session

from app.models.patient import Patient


class PatientRepository:

    @staticmethod
    def create(db: Session, patient: Patient):
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient

    @staticmethod
    def get_all(db: Session):
        return db.query(Patient).all()

    @staticmethod
    def get_by_id(db: Session, patient_id: int):
        return (
            db.query(Patient)
            .filter(Patient.id == patient_id)
            .first()
        )

    @staticmethod
    def get_by_email(db: Session, email: str):
        return (
            db.query(Patient)
            .filter(Patient.email == email)
            .first()
        )

    @staticmethod
    def get_by_phone(db: Session, phone: str):
        return (
            db.query(Patient)
            .filter(Patient.phone == phone)
            .first()
        )

    @staticmethod
    def get_by_name(db: Session, first_name: str, last_name: str):
        return (
            db.query(Patient)
            .filter(
                Patient.first_name == first_name,
                Patient.last_name == last_name
            )
            .first()
        )

    @staticmethod
    def get_or_create(
        db: Session,
        full_name: str,
        hospital_id: int
    ):

        names = full_name.split()

        first_name = names[0]

        last_name = " ".join(names[1:]) if len(names) > 1 else ""

        patient = PatientRepository.get_by_name(
            db,
            first_name,
            last_name
        )

        if patient:
            return patient

        patient = Patient(
            hospital_id=hospital_id,
            patient_code="PAT-" + first_name[:3].upper(),
            first_name=first_name,
            middle_name="",
            last_name=last_name,
            gender="Unknown",
            date_of_birth="2000-01-01",
            phone="0000000000",
            alternate_phone="",
            email=f"{first_name.lower()}@patient.com",
            blood_group="Unknown",
            address="Unknown",
            city="Unknown",
            state="Unknown",
            country="India",
            postal_code="000000",
            emergency_contact_name="Unknown",
            emergency_contact_phone="0000000000",
            emergency_contact_relation="Unknown"
        )

        return PatientRepository.create(
            db,
            patient
        )