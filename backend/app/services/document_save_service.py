from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ingestion.medical_record_doc import MedicalRecordDocument

from app.repositories.hospital_document_repository import HospitalDocumentRepository
from app.repositories.department_document_repository import DepartmentDocumentRepository
from app.repositories.doctor_document_repository import DoctorDocumentRepository
from app.repositories.patient_document_repository import PatientDocumentRepository
from app.repositories.medical_record_document_repository import MedicalRecordDocumentRepository


class DocumentSaveService:

    @staticmethod
    def save(db: Session, entities: dict):

        # -----------------------------
        # Hospital
        # -----------------------------
        hospital_name = entities.get("hospital") or settings.DEFAULT_HOSPITAL_NAME

        hospital = HospitalDocumentRepository.get_or_create(
            db,
            hospital_name
        )

        # -----------------------------
        # Department
        # -----------------------------

        department = DepartmentDocumentRepository.get_or_create(
            db=db,
            name=entities.get("department", "General"),
            hospital_id=hospital.id
        )

        # -----------------------------
        # Doctor
        # -----------------------------

        doctor = DoctorDocumentRepository.get_or_create(
            db=db,
            name=entities.get("doctor", "Unknown Doctor"),
            department_id=department.id
        )

        # -----------------------------
        # Patient
        # -----------------------------

        patient = PatientDocumentRepository.get_or_create(
            db=db,
            name=entities.get("patient", "Unknown Patient"),
            hospital_id=hospital.id
        )

        # -----------------------------
        # Medical Record
        # -----------------------------

        MedicalRecordDocumentRepository.get_or_create(
            db=db,
            patient_id=patient.id,
            doctor_id=doctor.id,
            diagnosis=", ".join(entities.get("diagnosis", [])),
            symptoms=", ".join(entities.get("symptoms", [])),
            medicines=", ".join(entities.get("medicines", [])),
            lab_tests=", ".join(entities.get("lab_tests", [])),
            follow_up=entities.get("follow_up", "")
        )
        return patient