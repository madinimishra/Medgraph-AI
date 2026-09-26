"""Imports a real FHIR R4 Bundle (the actual data-exchange standard
real hospitals and EHR systems use - not a made-up format) and maps it
into the SAME graph schema used by the Synthea CSV pipeline (Patient,
Organization, Provider, Encounter, Condition, Medication, Observation
nodes with the same relationship names). This is deliberate: it means
a FHIR-sourced patient becomes queryable through the exact same chat
agent, patient explorer, and network analysis as everything else in
the graph, with no separate code path needed downstream.

Synthea itself can export FHIR directly (as an alternative to the CSV
export used elsewhere in this project) - so this importer is the
bridge from "synthetic CSV dataset" to "the format real EHR systems
actually speak", which is the concrete gap this closes.

Supported resource types: Patient, Organization, Practitioner,
Encounter, Condition, MedicationRequest / MedicationStatement,
Observation. This covers the core clinical resources this app's graph
models - FHIR itself defines 140+ resource types, most of which don't
map onto anything this app represents.

HONESTY NOTE: this handles the common/typical field shapes (the ones
Synthea's own FHIR export and most real bundles use), not every legal
variation FHIR's spec allows (e.g. Period vs dateTime, CodeableConcept
vs plain string, contained vs referenced resources). A production
FHIR ingester would need a proper FHIR validation/parsing library
(e.g. `fhir.resources`) for full spec coverage.
"""

from app.graph.falkor_client import FalkorGraph
from app.core.config import settings


def _first(lst, default=None):
    return lst[0] if lst else default


def _patient_name(resource: dict) -> tuple[str, str]:
    name = _first(resource.get("name", []), {})
    given = _first(name.get("given", []), "")
    family = name.get("family", "")
    return given, family


def _reference_id(reference_obj: dict) -> str:
    """FHIR references look like {"reference": "Patient/abc-123"} -
    pull out just the id part."""
    ref = (reference_obj or {}).get("reference", "")
    return ref.split("/")[-1] if "/" in ref else ref


def _coding_text(codeable_concept: dict) -> str:
    if not codeable_concept:
        return ""
    if codeable_concept.get("text"):
        return codeable_concept["text"]
    coding = _first(codeable_concept.get("coding", []), {})
    return coding.get("display") or coding.get("code") or ""


class FHIRImportError(Exception):
    pass


class FHIRImporter:

    def __init__(self, graph_name: str = None):
        self.graph = FalkorGraph(graph_name=graph_name or settings.FALKOR_SYNTHEA_GRAPH)

    def import_bundle(self, bundle: dict) -> dict:

        if bundle.get("resourceType") != "Bundle":
            raise FHIRImportError(
                "Not a FHIR Bundle (expected resourceType 'Bundle', "
                f"got {bundle.get('resourceType')!r})"
            )

        by_type = {}
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")
            if resource_type:
                by_type.setdefault(resource_type, []).append(resource)

        counts = {
            "patients": self._import_patients(by_type.get("Patient", [])),
            "organizations": self._import_organizations(by_type.get("Organization", [])),
            "providers": self._import_practitioners(by_type.get("Practitioner", [])),
            "encounters": self._import_encounters(by_type.get("Encounter", [])),
            "conditions": self._import_conditions(by_type.get("Condition", [])),
            "medications": self._import_medications(
                by_type.get("MedicationRequest", []) + by_type.get("MedicationStatement", [])
            ),
            "observations": self._import_observations(by_type.get("Observation", [])),
        }

        return counts

    def _import_patients(self, resources: list[dict]) -> int:
        for r in resources:
            given, family = _patient_name(r)
            self.graph.query(
                """
                MERGE (p:Patient {id: $id})
                SET p.first_name = $first_name,
                    p.last_name = $last_name,
                    p.gender = $gender,
                    p.birthdate = $birthdate
                """,
                {
                    "id": r.get("id"),
                    "first_name": given,
                    "last_name": family,
                    "gender": r.get("gender"),
                    "birthdate": r.get("birthDate"),
                }
            )
        return len(resources)

    def _import_organizations(self, resources: list[dict]) -> int:
        for r in resources:
            self.graph.query(
                "MERGE (o:Organization {id: $id}) SET o.name = $name",
                {"id": r.get("id"), "name": r.get("name")}
            )
        return len(resources)

    def _import_practitioners(self, resources: list[dict]) -> int:
        for r in resources:
            given, family = _patient_name(r)
            name = f"{given} {family}".strip()
            self.graph.query(
                "MERGE (pr:Provider {id: $id}) SET pr.name = $name",
                {"id": r.get("id"), "name": name}
            )
        return len(resources)

    def _import_encounters(self, resources: list[dict]) -> int:
        for r in resources:
            patient_id = _reference_id(r.get("subject"))
            period = r.get("period", {})

            participant = _first(r.get("participant", []), {})
            provider_id = _reference_id(participant.get("individual", {})) if participant else None

            org_id = _reference_id(r.get("serviceProvider"))

            self.graph.query(
                """
                MERGE (e:Encounter {id: $id})
                SET e.start_time = $start_time,
                    e.stop_time = $stop_time,
                    e.encounter_class = $encounter_class,
                    e.description = $description
                """,
                {
                    "id": r.get("id"),
                    "start_time": period.get("start"),
                    "stop_time": period.get("end"),
                    "encounter_class": (r.get("class") or {}).get("code"),
                    "description": _coding_text(_first(r.get("type", []), {})),
                }
            )

            if patient_id:
                self.graph.query(
                    """
                    MATCH (p:Patient {id: $patient_id}), (e:Encounter {id: $id})
                    MERGE (p)-[:HAD_ENCOUNTER]->(e)
                    """,
                    {"patient_id": patient_id, "id": r.get("id")}
                )

            if provider_id:
                self.graph.query(
                    """
                    MATCH (pr:Provider {id: $provider_id}), (e:Encounter {id: $id})
                    MERGE (e)-[:PROVIDED_BY]->(pr)
                    """,
                    {"provider_id": provider_id, "id": r.get("id")}
                )

            if org_id:
                self.graph.query(
                    """
                    MATCH (o:Organization {id: $org_id}), (e:Encounter {id: $id})
                    MERGE (e)-[:AT]->(o)
                    """,
                    {"org_id": org_id, "id": r.get("id")}
                )

        return len(resources)

    def _import_conditions(self, resources: list[dict]) -> int:
        for index, r in enumerate(resources):
            patient_id = _reference_id(r.get("subject"))
            encounter_id = _reference_id(r.get("encounter"))
            condition_id = r.get("id") or f"fhir-condition-{index}"

            self.graph.query(
                """
                MERGE (c:Condition {id: $id})
                SET c.description = $description,
                    c.start_date = $start_date,
                    c.end_date = $end_date
                """,
                {
                    "id": condition_id,
                    "description": _coding_text(r.get("code", {})),
                    "start_date": r.get("onsetDateTime"),
                    "end_date": r.get("abatementDateTime"),
                }
            )

            if patient_id:
                self.graph.query(
                    """
                    MATCH (p:Patient {id: $patient_id}), (c:Condition {id: $id})
                    MERGE (p)-[:HAS_CONDITION]->(c)
                    """,
                    {"patient_id": patient_id, "id": condition_id}
                )

            if encounter_id:
                self.graph.query(
                    """
                    MATCH (e:Encounter {id: $encounter_id}), (c:Condition {id: $id})
                    MERGE (e)-[:HAS_CONDITION]->(c)
                    """,
                    {"encounter_id": encounter_id, "id": condition_id}
                )

        return len(resources)

    def _import_medications(self, resources: list[dict]) -> int:
        for index, r in enumerate(resources):
            patient_id = _reference_id(r.get("subject"))
            encounter_id = _reference_id(r.get("encounter") or r.get("context"))
            medication_id = r.get("id") or f"fhir-medication-{index}"

            description = (
                _coding_text(r.get("medicationCodeableConcept", {}))
                or r.get("medicationReference", {}).get("display", "")
            )

            self.graph.query(
                """
                MERGE (m:Medication {id: $id})
                SET m.description = $description,
                    m.start_time = $start_time
                """,
                {
                    "id": medication_id,
                    "description": description,
                    "start_time": r.get("authoredOn") or r.get("effectiveDateTime"),
                }
            )

            if patient_id:
                self.graph.query(
                    """
                    MATCH (p:Patient {id: $patient_id}), (m:Medication {id: $id})
                    MERGE (p)-[:TAKES]->(m)
                    """,
                    {"patient_id": patient_id, "id": medication_id}
                )

            if encounter_id:
                self.graph.query(
                    """
                    MATCH (m:Medication {id: $id}), (e:Encounter {id: $encounter_id})
                    MERGE (m)-[:DURING]->(e)
                    """,
                    {"encounter_id": encounter_id, "id": medication_id}
                )

        return len(resources)

    def _import_observations(self, resources: list[dict]) -> int:
        for index, r in enumerate(resources):
            patient_id = _reference_id(r.get("subject"))
            encounter_id = _reference_id(r.get("encounter"))
            observation_id = r.get("id") or f"fhir-observation-{index}"

            value_quantity = r.get("valueQuantity", {})
            value = value_quantity.get("value")
            units = value_quantity.get("unit")
            if value is None and r.get("valueString"):
                value = r.get("valueString")

            self.graph.query(
                """
                MERGE (o:Observation {id: $id})
                SET o.description = $description,
                    o.value = $value,
                    o.units = $units,
                    o.observation_date = $observation_date
                """,
                {
                    "id": observation_id,
                    "description": _coding_text(r.get("code", {})),
                    "value": str(value) if value is not None else None,
                    "units": units,
                    "observation_date": r.get("effectiveDateTime"),
                }
            )

            if patient_id:
                self.graph.query(
                    """
                    MATCH (p:Patient {id: $patient_id}), (o:Observation {id: $id})
                    MERGE (p)-[:HAS_OBSERVATION]->(o)
                    """,
                    {"patient_id": patient_id, "id": observation_id}
                )

            if encounter_id:
                self.graph.query(
                    """
                    MATCH (e:Encounter {id: $encounter_id}), (o:Observation {id: $id})
                    MERGE (e)-[:HAS_OBSERVATION]->(o)
                    """,
                    {"encounter_id": encounter_id, "id": observation_id}
                )

        return len(resources)
