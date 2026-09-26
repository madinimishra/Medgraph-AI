from sqlalchemy.orm import Session

from app.graph.falkor_client import FalkorGraph
from app.core.config import settings
from app.models.hospital import Hospital
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.medical_record import MedicalRecord


class HospitalGraphBuilder:

    def __init__(self):
        self.graph = FalkorGraph()
        self.synthea_graph = FalkorGraph(graph_name=settings.FALKOR_SYNTHEA_GRAPH)

    def build_graph(self, db: Session):
        """Rebuild the live 'hospital_graph' from the relational
        (Postgres) hospital / department / doctor / patient /
        medical_record CRUD tables."""

        for hospital in db.query(Hospital).all():
            self.graph.query(
                """
                MERGE (h:Hospital {id: $id})
                SET h.name = $name,
                    h.city = $city,
                    h.state = $state,
                    h.country = $country
                """,
                {
                    "id": hospital.id,
                    "name": hospital.hospital_name,
                    "city": hospital.city,
                    "state": hospital.state,
                    "country": hospital.country
                }
            )

        for department in db.query(Department).all():
            self.graph.query(
                """
                MATCH (h:Hospital {id: $hospital_id})
                MERGE (d:Department {id: $id})
                SET d.name = $name,
                    d.floor = $floor,
                    d.hod_name = $hod_name
                MERGE (h)-[:HAS_DEPARTMENT]->(d)
                """,
                {
                    "id": department.id,
                    "hospital_id": department.hospital_id,
                    "name": department.department_name,
                    "floor": department.floor,
                    "hod_name": department.hod_name
                }
            )

        for doctor in db.query(Doctor).all():
            self.graph.query(
                """
                MATCH (d:Department {id: $department_id})
                MERGE (doc:Doctor {id: $id})
                SET doc.name = $name,
                    doc.specialization = $specialization,
                    doc.qualification = $qualification,
                    doc.experience = $experience
                MERGE (d)-[:HAS_DOCTOR]->(doc)
                """,
                {
                    "id": doctor.id,
                    "department_id": doctor.department_id,
                    "name": doctor.full_name,
                    "specialization": doctor.specialization,
                    "qualification": doctor.qualification,
                    "experience": doctor.experience
                }
            )

        for patient in db.query(Patient).all():
            self.graph.query(
                """
                MATCH (h:Hospital {id: $hospital_id})
                MERGE (p:Patient {id: $id})
                SET p.name = $name,
                    p.gender = $gender,
                    p.city = $city,
                    p.state = $state
                MERGE (h)-[:HAS_PATIENT]->(p)
                """,
                {
                    "id": patient.id,
                    "hospital_id": patient.hospital_id,
                    "name": f"{patient.first_name} {patient.last_name}",
                    "gender": patient.gender,
                    "city": patient.city,
                    "state": patient.state
                }
            )

        for record in db.query(MedicalRecord).all():
            self.graph.query(
                """
                MATCH (doc:Doctor {id: $doctor_id})
                MATCH (p:Patient {id: $patient_id})
                MERGE (doc)-[:TREATS]->(p)
                """,
                {
                    "doctor_id": record.doctor_id,
                    "patient_id": record.patient_id
                }
            )

            for diagnosis in self._split(record.diagnosis):
                self.graph.query(
                    """
                    MATCH (p:Patient {id: $patient_id})
                    MERGE (d:Diagnosis {name: $name})
                    MERGE (p)-[:HAS_DIAGNOSIS]->(d)
                    """,
                    {"patient_id": record.patient_id, "name": diagnosis}
                )

            for symptom in self._split(record.symptoms):
                self.graph.query(
                    """
                    MATCH (p:Patient {id: $patient_id})
                    MERGE (s:Symptom {name: $name})
                    MERGE (p)-[:HAS_SYMPTOM]->(s)
                    """,
                    {"patient_id": record.patient_id, "name": symptom}
                )

            for medicine in self._split(record.prescription):
                self.graph.query(
                    """
                    MATCH (p:Patient {id: $patient_id})
                    MERGE (m:Medicine {name: $name})
                    MERGE (p)-[:TAKES_MEDICINE]->(m)
                    """,
                    {"patient_id": record.patient_id, "name": medicine}
                )

            for lab_test in self._split(record.lab_tests):
                self.graph.query(
                    """
                    MATCH (p:Patient {id: $patient_id})
                    MERGE (l:LabTest {name: $name})
                    MERGE (p)-[:HAS_LAB_TEST]->(l)
                    """,
                    {"patient_id": record.patient_id, "name": lab_test}
                )

    @staticmethod
    def _split(value: str):
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    def create_patient_graph(self, entities: dict, patient_id, document_id: str):
        """Writes an uploaded document's extracted patient into the SAME
        graph and schema as the Synthea dataset (Patient/Encounter/
        Organization/Provider/Condition/Medication/Observation, with the
        same relationship names), rather than a separate graph with its
        own ad-hoc schema. This is what makes an uploaded patient show
        up in the existing Patients search/journey/subgraph endpoints -
        they all read from FALKOR_SYNTHEA_GRAPH and expect this exact
        shape. IDs are prefixed with 'doc-' so they can never collide
        with Synthea's own ids."""

        graph_id = f"doc-{patient_id}"
        full_name = entities.get("patient") or "Unknown Patient"
        name_parts = full_name.rsplit(" ", 1)
        first_name = name_parts[0] if len(name_parts) > 1 else full_name
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        hospital = entities.get("hospital") or "Unknown Hospital"
        doctor = entities.get("doctor") or "Unknown Doctor"
        department = entities.get("department") or "General"
        encounter_id = f"doc-{document_id}-enc"

        self.synthea_graph.query(
            """
            MERGE (p:Patient {id: $patient_id})
            SET p.first_name = $first_name,
                p.last_name = $last_name,
                p.source = 'document'

            MERGE (o:Organization {id: $org_id})
            SET o.name = $hospital

            MERGE (pr:Provider {id: $provider_id})
            SET pr.name = $doctor, pr.speciality = $department

            MERGE (e:Encounter {id: $encounter_id})
            SET e.start_time = $uploaded_at,
                e.encounter_class = 'document',
                e.description = $description

            MERGE (p)-[:HAD_ENCOUNTER]->(e)
            MERGE (e)-[:PROVIDED_BY]->(pr)
            MERGE (e)-[:AT]->(o)
            """,
            {
                "patient_id": graph_id,
                "first_name": first_name,
                "last_name": last_name,
                "org_id": f"doc-org-{hospital}",
                "hospital": hospital,
                "provider_id": f"doc-provider-{doctor}",
                "doctor": doctor,
                "department": department,
                "encounter_id": encounter_id,
                "uploaded_at": entities.get("uploaded_at") or "",
                "description": ", ".join(entities.get("diagnosis", [])) or "Document-sourced encounter",
            }
        )

        for index, diagnosis in enumerate(entities.get("diagnosis", [])):
            condition_id = f"{encounter_id}-cond-{index}"
            self.synthea_graph.query(
                """
                MATCH (p:Patient {id: $patient_id}), (e:Encounter {id: $encounter_id})
                MERGE (c:Condition {id: $condition_id})
                SET c.description = $description
                MERGE (p)-[:HAS_CONDITION]->(c)
                MERGE (e)-[:HAS_CONDITION]->(c)
                """,
                {"patient_id": graph_id, "encounter_id": encounter_id,
                 "condition_id": condition_id, "description": diagnosis}
            )

        for index, medicine in enumerate(entities.get("medicines", [])):
            medication_id = f"{encounter_id}-med-{index}"
            self.synthea_graph.query(
                """
                MATCH (p:Patient {id: $patient_id}), (e:Encounter {id: $encounter_id})
                MERGE (m:Medication {id: $medication_id})
                SET m.description = $description
                MERGE (p)-[:TAKES]->(m)
                MERGE (m)-[:DURING]->(e)
                """,
                {"patient_id": graph_id, "encounter_id": encounter_id,
                 "medication_id": medication_id, "description": medicine}
            )

        for index, lab_test in enumerate(entities.get("lab_tests", [])):
            observation_id = f"{encounter_id}-obs-{index}"
            self.synthea_graph.query(
                """
                MATCH (p:Patient {id: $patient_id}), (e:Encounter {id: $encounter_id})
                MERGE (obs:Observation {id: $observation_id})
                SET obs.description = $description
                MERGE (p)-[:HAS_OBSERVATION]->(obs)
                MERGE (e)-[:HAS_OBSERVATION]->(obs)
                """,
                {"patient_id": graph_id, "encounter_id": encounter_id,
                 "observation_id": observation_id, "description": lab_test}
            )

        return graph_id