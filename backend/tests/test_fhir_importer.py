"""Integration test for FHIRImporter against a real (running) FalkorDB
instance - deliberately using an isolated test graph name, never the
shared medgraph_synthea graph, so this never mutates the counts the
eval benchmark and demo rely on. Requires FalkorDB to be reachable;
skipped automatically if it isn't (e.g. in a CI environment without a
database service configured)."""

import json
import os

import pytest

from app.graph.falkor_client import FalkorGraph
from app.ingestion.fhir_importer import FHIRImporter, FHIRImportError

TEST_GRAPH_NAME = "medgraph_fhir_test"

FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "sample_fhir_bundle.json"
)


def _falkordb_available():
    try:
        FalkorGraph(graph_name=TEST_GRAPH_NAME).query("RETURN 1")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _falkordb_available(), reason="FalkorDB is not reachable"
)


def _delete_if_exists(graph):
    try:
        graph.graph.delete()
    except Exception:
        pass  # graph doesn't exist yet - nothing to clean up


@pytest.fixture
def clean_test_graph():
    graph = FalkorGraph(graph_name=TEST_GRAPH_NAME)
    _delete_if_exists(graph)
    yield graph
    _delete_if_exists(graph)


def _load_fixture():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


class TestFHIRImporter:

    def test_import_reports_a_count_per_resource_type(self, clean_test_graph):
        importer = FHIRImporter(graph_name=TEST_GRAPH_NAME)
        counts = importer.import_bundle(_load_fixture())

        assert counts["patients"] == 1
        assert counts["organizations"] == 1
        assert counts["providers"] == 1
        assert counts["encounters"] == 1
        assert counts["conditions"] == 1
        assert counts["medications"] == 1
        assert counts["observations"] == 1

    def test_imported_patient_is_queryable_by_name(self, clean_test_graph):
        importer = FHIRImporter(graph_name=TEST_GRAPH_NAME)
        importer.import_bundle(_load_fixture())

        result = clean_test_graph.query(
            "MATCH (p:Patient {id: 'fhir-patient-001'}) "
            "RETURN p.first_name, p.last_name, p.gender"
        )
        assert result.result_set[0] == ["Rohan", "Fernandes", "male"]

    def test_encounter_is_linked_to_patient_provider_and_organization(self, clean_test_graph):
        importer = FHIRImporter(graph_name=TEST_GRAPH_NAME)
        importer.import_bundle(_load_fixture())

        result = clean_test_graph.query(
            """
            MATCH (p:Patient)-[:HAD_ENCOUNTER]->(e:Encounter)-[:AT]->(o:Organization)
            MATCH (e)-[:PROVIDED_BY]->(pr:Provider)
            RETURN p.first_name, o.name, pr.name
            """
        )
        assert result.result_set[0] == ["Rohan", "Riverside General Hospital", "Maria Alvarez"]

    def test_condition_medication_and_observation_are_linked_to_the_patient(self, clean_test_graph):
        importer = FHIRImporter(graph_name=TEST_GRAPH_NAME)
        importer.import_bundle(_load_fixture())

        result = clean_test_graph.query(
            """
            MATCH (p:Patient)-[:HAS_CONDITION]->(c:Condition)
            MATCH (p)-[:TAKES]->(m:Medication)
            MATCH (p)-[:HAS_OBSERVATION]->(o:Observation)
            RETURN c.description, m.description, o.value, o.units
            """
        )
        assert result.result_set[0] == [
            "Acute appendicitis (disorder)",
            "Ceftriaxone 1g IV",
            "14.2",
            "10*3/uL",
        ]

    def test_a_second_import_of_the_same_bundle_does_not_duplicate_nodes(self, clean_test_graph):
        importer = FHIRImporter(graph_name=TEST_GRAPH_NAME)
        importer.import_bundle(_load_fixture())
        importer.import_bundle(_load_fixture())

        result = clean_test_graph.query("MATCH (p:Patient) RETURN count(p)")
        assert result.result_set[0][0] == 1

    def test_rejects_something_that_is_not_a_fhir_bundle(self, clean_test_graph):
        importer = FHIRImporter(graph_name=TEST_GRAPH_NAME)
        with pytest.raises(FHIRImportError):
            importer.import_bundle({"resourceType": "Patient"})
