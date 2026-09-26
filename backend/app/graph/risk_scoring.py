"""A transparent, rule-based risk score computed from graph-derived
features (medication count, emergency-visit history, condition count,
age).

IMPORTANT / HONESTY NOTE: this is a heuristic scoring formula, not a
trained or clinically validated predictive model. Synthea has no real
outcome labels (e.g. actual readmissions) to train or validate a real
risk model against, so building one and presenting it as clinically
predictive would be dishonest. What's implemented here is closer to
what a hospital's own rule-based alerting system does - explicit,
auditable point weights - and every score returned includes the exact
factors that produced it, precisely so it's never a black box."""

from datetime import date, datetime

from app.graph.queries import get_synthea_graph

POLYPHARMACY_THRESHOLD = 5
EMERGENCY_ENCOUNTER_POINTS = 3
POLYPHARMACY_POINTS_PER_EXTRA_MED = 2
CHRONIC_CONDITION_POINTS = 1
AGE_65_PLUS_POINTS = 2

HIGH_RISK_THRESHOLD = 10
MODERATE_RISK_THRESHOLD = 5


def _parse_age(birthdate: str) -> int:
    try:
        born = datetime.fromisoformat(birthdate.split(" ")[0]).date()
    except (ValueError, AttributeError):
        return None

    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def get_patient_risk(patient_id: str) -> dict:

    graph = get_synthea_graph()

    patient_result = graph.query(
        "MATCH (p:Patient {id: $id}) RETURN p.birthdate AS birthdate",
        {"id": patient_id}
    )
    if not patient_result.result_set:
        return None

    birthdate = patient_result.result_set[0][0]
    age = _parse_age(birthdate) if birthdate else None

    med_result = graph.query(
        """
        MATCH (p:Patient {id: $id})-[:TAKES]->(m:Medication)
        RETURN count(DISTINCT m.description) AS medication_count
        """,
        {"id": patient_id}
    )
    medication_count = med_result.result_set[0][0] if med_result.result_set else 0

    emergency_result = graph.query(
        """
        MATCH (p:Patient {id: $id})-[:HAD_ENCOUNTER]->(e:Encounter)
        WHERE e.encounter_class = 'emergency'
        RETURN count(e) AS emergency_count
        """,
        {"id": patient_id}
    )
    emergency_count = emergency_result.result_set[0][0] if emergency_result.result_set else 0

    condition_result = graph.query(
        """
        MATCH (p:Patient {id: $id})-[:HAS_CONDITION]->(c:Condition)
        WHERE c.description CONTAINS '(disorder)'
        RETURN count(DISTINCT c.description) AS condition_count
        """,
        {"id": patient_id}
    )
    condition_count = condition_result.result_set[0][0] if condition_result.result_set else 0

    factors = []
    score = 0

    if medication_count > POLYPHARMACY_THRESHOLD:
        extra_meds = medication_count - POLYPHARMACY_THRESHOLD
        points = extra_meds * POLYPHARMACY_POINTS_PER_EXTRA_MED
        score += points
        factors.append({
            "factor": "polypharmacy",
            "detail": f"{medication_count} distinct medications (threshold {POLYPHARMACY_THRESHOLD})",
            "points": points,
        })

    if emergency_count > 0:
        points = emergency_count * EMERGENCY_ENCOUNTER_POINTS
        score += points
        factors.append({
            "factor": "emergency_visit_history",
            "detail": f"{emergency_count} emergency encounter(s)",
            "points": points,
        })

    if condition_count > 0:
        points = condition_count * CHRONIC_CONDITION_POINTS
        score += points
        factors.append({
            "factor": "condition_burden",
            "detail": f"{condition_count} distinct diagnosed disorder(s)",
            "points": points,
        })

    if age is not None and age >= 65:
        score += AGE_65_PLUS_POINTS
        factors.append({
            "factor": "age_65_plus",
            "detail": f"age {age}",
            "points": AGE_65_PLUS_POINTS,
        })

    if score >= HIGH_RISK_THRESHOLD:
        risk_level = "high"
    elif score >= MODERATE_RISK_THRESHOLD:
        risk_level = "moderate"
    else:
        risk_level = "low"

    return {
        "patient_id": patient_id,
        "age": age,
        "medication_count": medication_count,
        "emergency_encounter_count": emergency_count,
        "condition_count": condition_count,
        "risk_score": score,
        "risk_level": risk_level,
        "factors": factors,
        "disclaimer": (
            "This is a transparent, rule-based heuristic score for "
            "demonstration purposes, not a clinically validated "
            "predictive model."
        ),
    }
