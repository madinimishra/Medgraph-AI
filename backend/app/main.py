from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.doctors import router as doctor_router
from app.api.v1.auth import router as auth_router
from app.database.base import Base
from app.database.postgres import engine
from app.api.v1.patients import router as patient_router
import app.models
from app.api.v1.departments import router as department_router
from app.api.v1.appointments import router as appointment_router
from app.api.v1.medical_records import router as medical_record_router
from app.api.v1.graph import router as graph_router
from app.api.v1.hospitals import router as hospital_router
from app.api.v1.graph import router as graph_router
from app.api.v1.document import router as document_router
from app.api.v1.chat import router as chat_router
from app.api.v1.observability import router as observability_router
from app.api.v1.network import router as network_router
from app.api.v1.audit import router as audit_router
from app.api.v1.fhir import router as fhir_router
from app.api.v1.admin import router as admin_router
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MedGraph AI"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(patient_router)
app.include_router(doctor_router)
app.include_router(department_router)
app.include_router(appointment_router)
app.include_router(medical_record_router)
app.include_router(graph_router)
app.include_router(hospital_router)
app.include_router(document_router)
app.include_router(chat_router)
app.include_router(observability_router)
app.include_router(network_router)
app.include_router(audit_router)
app.include_router(fhir_router)
app.include_router(admin_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to MedGraph AI 🚀"
    }