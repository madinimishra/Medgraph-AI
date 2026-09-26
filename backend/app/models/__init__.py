from .user import User
from app.models.patient import Patient
from .doctor import Doctor
from .department import Department
from app.models.appointment import Appointment
from app.models.medical_record import MedicalRecord
from app.models.hospital import Hospital
from app.models.audit_log import AuditLog

# -----------------------------
# Ingestion Models
# -----------------------------
from app.models.ingestion.hospital_doc import HospitalDocument
from app.models.ingestion.department_doc import DepartmentDocument
from app.models.ingestion.doctor_doc import DoctorDocument
from app.models.ingestion.patient_doc import PatientDocument
from app.models.ingestion.medical_record_doc import MedicalRecordDocument