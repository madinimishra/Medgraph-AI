"""Tests for the scoring logic used by the eval benchmark and the
graph/vector/hybrid comparison harness. Getting this wrong would mean
the benchmark reports a false accuracy number - these are worth
protecting even though they're "just test infrastructure"."""

from app.eval.run_eval import score
from app.eval.compare_retrieval import _answer_contains_expected


class TestBenchmarkScore:

    def test_scalar_equals_passes_when_the_value_is_present(self):
        rows = [{"total_patients": 1163}]
        passed, _ = score(rows, error=None, check={"type": "scalar_equals", "value": 1163})
        assert passed is True

    def test_scalar_equals_fails_when_the_value_is_absent(self):
        rows = [{"total_patients": 42}]
        passed, _ = score(rows, error=None, check={"type": "scalar_equals", "value": 1163})
        assert passed is False

    def test_scalar_equals_correctly_matches_a_real_zero(self):
        # A returned 0 is a real answer, not "no data" - the scorer must
        # not treat an empty-looking value as a missing one.
        rows = [{"provider_count": 0}]
        passed, _ = score(rows, error=None, check={"type": "scalar_equals", "value": 0})
        assert passed is True

    def test_contains_matches_case_insensitively(self):
        rows = [{"hospital": "MOUNT AUBURN HOSPITAL"}]
        passed, _ = score(
            rows, error=None,
            check={"type": "contains", "values": ["mount auburn hospital"]}
        )
        assert passed is True

    def test_min_rows_fails_when_too_few_rows_returned(self):
        rows = [{"x": 1}]
        passed, _ = score(rows, error=None, check={"type": "min_rows", "value": 5})
        assert passed is False

    def test_an_agent_exception_fails_a_scalar_check(self):
        passed, reason = score(
            [], error="query timed out",
            check={"type": "scalar_equals", "value": 10}
        )
        assert passed is False
        assert "exception" in reason

    def test_expect_empty_or_error_passes_on_empty_rows(self):
        passed, _ = score([], error=None, check={"type": "expect_empty_or_error"})
        assert passed is True

    def test_expect_empty_or_error_passes_when_the_agent_raised(self):
        passed, _ = score([], error="could not generate a valid query", check={"type": "expect_empty_or_error"})
        assert passed is True

    def test_expect_empty_or_error_fails_if_rows_were_actually_returned(self):
        passed, _ = score(
            [{"doctor": "Dr. Smith"}], error=None,
            check={"type": "expect_empty_or_error"}
        )
        assert passed is False


class TestComparisonAnswerCheck:

    def test_scalar_equals_ignores_comma_formatting_in_the_answer_text(self):
        # Real bug caught during development: "1,163" didn't match a
        # literal "1163" substring check.
        answer = "There are 1,163 patients in total."
        assert _answer_contains_expected(answer, {"type": "scalar_equals", "value": 1163}) is True

    def test_contains_matches_any_of_the_accepted_values(self):
        answer = "Mount Auburn Hospital and Cambridge Health Alliance share 54 patients."
        check = {"type": "contains", "values": ["cambridge health alliance"]}
        assert _answer_contains_expected(answer, check) is True

    def test_min_rows_treats_a_refusal_phrase_as_a_failure(self):
        answer = "I don't have that information available."
        assert _answer_contains_expected(answer, {"type": "min_rows", "value": 1}) is False
