"""Tests for the safety/RBAC checks GraphRAGAgent runs on generated
Cypher BEFORE executing it. These are pure functions (no LLM call, no
database connection needed), which is exactly why they're worth testing
directly - broken safety logic here would go straight through to the
database."""

from app.agents.graph_agent import GraphRAGAgent


class TestIsReadOnly:

    def test_a_plain_match_return_is_allowed(self):
        cypher = "MATCH (p:Patient) RETURN count(p)"
        assert GraphRAGAgent.is_read_only(cypher) is True

    def test_a_query_with_where_and_order_by_is_allowed(self):
        cypher = (
            "MATCH (p:Patient)-[:HAS_CONDITION]->(c:Condition) "
            "WHERE c.description CONTAINS 'diabetes' "
            "RETURN p.first_name ORDER BY p.first_name LIMIT 10"
        )
        assert GraphRAGAgent.is_read_only(cypher) is True

    def test_delete_is_blocked(self):
        cypher = "MATCH (p:Patient) DELETE p"
        assert GraphRAGAgent.is_read_only(cypher) is False

    def test_merge_is_blocked(self):
        cypher = "MERGE (p:Patient {id: '123'}) RETURN p"
        assert GraphRAGAgent.is_read_only(cypher) is False

    def test_create_is_blocked(self):
        cypher = "CREATE (p:Patient {id: '999'}) RETURN p"
        assert GraphRAGAgent.is_read_only(cypher) is False

    def test_set_is_blocked(self):
        cypher = "MATCH (p:Patient) SET p.first_name = 'hacked' RETURN p"
        assert GraphRAGAgent.is_read_only(cypher) is False

    def test_detach_delete_is_blocked(self):
        cypher = "MATCH (p:Patient) DETACH DELETE p"
        assert GraphRAGAgent.is_read_only(cypher) is False

    def test_blocked_keywords_are_caught_regardless_of_case(self):
        cypher = "match (p:Patient) delete p"
        assert GraphRAGAgent.is_read_only(cypher) is False


class TestIsScopedToProvider:

    PROVIDER_ID = "30e7ac1b-26fe-3097-8dbb-9672ae7dfb00"

    def test_a_query_with_no_patient_node_needs_no_scoping(self):
        cypher = "MATCH (o:Organization) RETURN o.name"
        assert GraphRAGAgent.is_scoped_to_provider(cypher, self.PROVIDER_ID) is True

    def test_a_patient_query_naming_the_providers_id_passes(self):
        cypher = (
            "MATCH (p:Patient)-[:HAD_ENCOUNTER]->(:Encounter)-[:PROVIDED_BY]->"
            f"(:Provider {{id: '{self.PROVIDER_ID}'}}) RETURN count(p)"
        )
        assert GraphRAGAgent.is_scoped_to_provider(cypher, self.PROVIDER_ID) is True

    def test_a_patient_query_missing_the_providers_id_fails(self):
        # This is the important case: a query that touches Patient data
        # but was NOT constrained to this doctor's own provider must be
        # rejected, not silently allowed to return every patient.
        cypher = "MATCH (p:Patient) RETURN count(p)"
        assert GraphRAGAgent.is_scoped_to_provider(cypher, self.PROVIDER_ID) is False

    def test_a_patient_query_naming_a_different_providers_id_fails(self):
        cypher = (
            "MATCH (p:Patient)-[:HAD_ENCOUNTER]->(:Encounter)-[:PROVIDED_BY]->"
            "(:Provider {id: 'some-other-provider-id'}) RETURN count(p)"
        )
        assert GraphRAGAgent.is_scoped_to_provider(cypher, self.PROVIDER_ID) is False
