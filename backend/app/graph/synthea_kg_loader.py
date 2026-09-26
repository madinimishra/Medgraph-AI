import psycopg2
from falkordb import FalkorDB

from app.core.config import settings


# --------------------------------------------------
# Connections
# --------------------------------------------------

def get_postgres_connection():
    return psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD
    )


def get_falkor_graph():
    db = FalkorDB(
        host=settings.FALKOR_HOST,
        port=settings.FALKOR_PORT
    )

    return db.select_graph(settings.FALKOR_SYNTHEA_GRAPH)


# --------------------------------------------------
# Load Patients
# --------------------------------------------------

def load_patients(graph):

    print("[INFO] Loading patients from PostgreSQL...")

    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            first_name,
            last_name,
            birthdate,
            deathdate,
            gender,
            race,
            ethnicity,
            birthplace,
            address,
            city,
            state,
            county,
            zip,
            latitude,
            longitude,
            healthcare_expenses,
            healthcare_coverage
        FROM synthea.patients
    """)

    patients = cursor.fetchall()

    print(f"[INFO] Found {len(patients):,} patients")

    query = """
        MERGE (p:Patient {id: $id})
        SET
            p.first_name = $first_name,
            p.last_name = $last_name,
            p.birthdate = $birthdate,
            p.deathdate = $deathdate,
            p.gender = $gender,
            p.race = $race,
            p.ethnicity = $ethnicity,
            p.birthplace = $birthplace,
            p.address = $address,
            p.city = $city,
            p.state = $state,
            p.county = $county,
            p.zip = $zip,
            p.latitude = $latitude,
            p.longitude = $longitude,
            p.healthcare_expenses = $healthcare_expenses,
            p.healthcare_coverage = $healthcare_coverage
    """

    for patient in patients:

        (
            patient_id,
            first_name,
            last_name,
            birthdate,
            deathdate,
            gender,
            race,
            ethnicity,
            birthplace,
            address,
            city,
            state,
            county,
            zip_code,
            latitude,
            longitude,
            healthcare_expenses,
            healthcare_coverage
        ) = patient

        graph.query(
            query,
            {
                "id": str(patient_id),
                "first_name": first_name,
                "last_name": last_name,
                "birthdate": str(birthdate) if birthdate else None,
                "deathdate": str(deathdate) if deathdate else None,
                "gender": gender,
                "race": race,
                "ethnicity": ethnicity,
                "birthplace": birthplace,
                "address": address,
                "city": city,
                "state": state,
                "county": county,
                "zip": str(zip_code) if zip_code else None,
                "latitude": latitude,
                "longitude": longitude,
                "healthcare_expenses": healthcare_expenses,
                "healthcare_coverage": healthcare_coverage
            }
        )

    cursor.close()
    conn.close()

    print(f"[SUCCESS] Loaded {len(patients):,} Patient nodes")

# --------------------------------------------------
# Load Organizations
# --------------------------------------------------

def load_organizations(graph):

    print("[INFO] Loading organizations from PostgreSQL...")

    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            address,
            city,
            state,
            zip,
            latitude,
            longitude,
            phone,
            revenue,
            utilization
        FROM synthea.organizations
    """)

    organizations = cursor.fetchall()

    print(f"[INFO] Found {len(organizations):,} organizations")

    query = """
        MERGE (o:Organization {id: $id})
        SET
            o.name = $name,
            o.address = $address,
            o.city = $city,
            o.state = $state,
            o.zip = $zip,
            o.latitude = $latitude,
            o.longitude = $longitude,
            o.phone = $phone,
            o.revenue = $revenue,
            o.utilization = $utilization
    """

    for organization in organizations:

        (
            org_id,
            name,
            address,
            city,
            state,
            zip_code,
            latitude,
            longitude,
            phone,
            revenue,
            utilization
        ) = organization

        graph.query(
            query,
            {
                "id": str(org_id),
                "name": name,
                "address": address,
                "city": city,
                "state": state,
                "zip": str(zip_code) if zip_code else None,
                "latitude": latitude,
                "longitude": longitude,
                "phone": phone,
                "revenue": revenue,
                "utilization": utilization
            }
        )

    cursor.close()
    conn.close()

    print(
        f"[SUCCESS] Loaded {len(organizations):,} Organization nodes"
    )

# --------------------------------------------------
# Load Providers
# --------------------------------------------------

def load_providers(graph):

    print("[INFO] Loading providers from PostgreSQL...")

    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            organization_id,
            name,
            gender,
            speciality,
            address,
            city,
            state,
            zip,
            latitude,
            longitude,
            utilization
        FROM synthea.providers
    """)

    providers = cursor.fetchall()

    print(f"[INFO] Found {len(providers):,} providers")

    query = """
        MERGE (p:Provider {id: $id})
        SET
            p.name = $name,
            p.gender = $gender,
            p.speciality = $speciality,
            p.address = $address,
            p.city = $city,
            p.state = $state,
            p.zip = $zip,
            p.latitude = $latitude,
            p.longitude = $longitude,
            p.utilization = $utilization
    """

    for provider in providers:

        (
            provider_id,
            organization_id,
            name,
            gender,
            speciality,
            address,
            city,
            state,
            zip_code,
            latitude,
            longitude,
            utilization
        ) = provider

        graph.query(
            query,
            {
                "id": str(provider_id),
                "name": name,
                "gender": gender,
                "speciality": speciality,
                "address": address,
                "city": city,
                "state": state,
                "zip": str(zip_code) if zip_code else None,
                "latitude": latitude,
                "longitude": longitude,
                "utilization": utilization
            }
        )

        # Connect provider to organization
        if organization_id:

            graph.query(
                """
                MATCH (p:Provider {id: $provider_id})
                MATCH (o:Organization {id: $organization_id})
                MERGE (p)-[:WORKS_AT]->(o)
                """,
                {
                    "provider_id": str(provider_id),
                    "organization_id": str(organization_id)
                }
            )

    cursor.close()
    conn.close()

    print(
        f"[SUCCESS] Loaded {len(providers):,} Provider nodes"
    )

# --------------------------------------------------
# Load Encounters
# --------------------------------------------------

# --------------------------------------------------
# Load Encounters - BATCHED
# --------------------------------------------------

def load_encounters(graph):

    print("[INFO] Loading encounters from PostgreSQL...")

    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            start_time,
            stop_time,
            patient_id,
            organization_id,
            provider_id,
            payer_id,
            encounter_class,
            code,
            description,
            base_encounter_cost,
            total_claim_cost,
            payer_coverage,
            reason_code,
            reason_description
        FROM synthea.encounters
    """)

    encounters = cursor.fetchall()

    print(f"[INFO] Found {len(encounters):,} encounters")

    # --------------------------------------------------
    # Convert PostgreSQL rows into FalkorDB parameters
    # --------------------------------------------------

    encounter_rows = []

    for encounter in encounters:

        (
            encounter_id,
            start_time,
            stop_time,
            patient_id,
            organization_id,
            provider_id,
            payer_id,
            encounter_class,
            code,
            description,
            base_encounter_cost,
            total_claim_cost,
            payer_coverage,
            reason_code,
            reason_description
        ) = encounter

        encounter_rows.append({
            "id": str(encounter_id),
            "start_time": str(start_time) if start_time else None,
            "stop_time": str(stop_time) if stop_time else None,
            "patient_id": str(patient_id) if patient_id else None,
            "organization_id": str(organization_id) if organization_id else None,
            "provider_id": str(provider_id) if provider_id else None,
            "payer_id": str(payer_id) if payer_id else None,
            "encounter_class": encounter_class,
            "code": str(code) if code else None,
            "description": description,
            "base_encounter_cost": float(base_encounter_cost) if base_encounter_cost is not None else None,
            "total_claim_cost": float(total_claim_cost) if total_claim_cost is not None else None,
            "payer_coverage": float(payer_coverage) if payer_coverage is not None else None,
            "reason_code": str(reason_code) if reason_code else None,
            "reason_description": reason_description
        })

    # --------------------------------------------------
    # Batch size
    # --------------------------------------------------

    BATCH_SIZE = 500

    total = len(encounter_rows)

    for start in range(0, total, BATCH_SIZE):

        batch = encounter_rows[start:start + BATCH_SIZE]

        print(
            f"[INFO] Processing encounters "
            f"{start + 1:,}-{min(start + BATCH_SIZE, total):,}"
            f"/{total:,}"
        )

        # --------------------------------------------------
        # Create Encounter nodes
        # --------------------------------------------------

        graph.query(
            """
            UNWIND $rows AS row

            MERGE (e:Encounter {id: row.id})

            SET
                e.start_time = row.start_time,
                e.stop_time = row.stop_time,
                e.encounter_class = row.encounter_class,
                e.code = row.code,
                e.description = row.description,
                e.base_encounter_cost = row.base_encounter_cost,
                e.total_claim_cost = row.total_claim_cost,
                e.payer_coverage = row.payer_coverage,
                e.reason_code = row.reason_code,
                e.reason_description = row.reason_description
            """,
            {
                "rows": batch
            }
        )

        # --------------------------------------------------
        # Patient -> Encounter
        # --------------------------------------------------

        graph.query(
            """
            UNWIND $rows AS row

            MATCH (p:Patient {id: row.patient_id})
            MATCH (e:Encounter {id: row.id})

            MERGE (p)-[:HAD_ENCOUNTER]->(e)
            """,
            {
                "rows": [
                    row for row in batch
                    if row["patient_id"]
                ]
            }
        )

        # --------------------------------------------------
        # Encounter -> Provider
        # --------------------------------------------------

        graph.query(
            """
            UNWIND $rows AS row

            MATCH (e:Encounter {id: row.id})
            MATCH (pr:Provider {id: row.provider_id})

            MERGE (e)-[:PROVIDED_BY]->(pr)
            """,
            {
                "rows": [
                    row for row in batch
                    if row["provider_id"]
                ]
            }
        )

        # --------------------------------------------------
        # Encounter -> Organization
        # --------------------------------------------------

        graph.query(
            """
            UNWIND $rows AS row

            MATCH (e:Encounter {id: row.id})
            MATCH (o:Organization {id: row.organization_id})

            MERGE (e)-[:AT]->(o)
            """,
            {
                "rows": [
                    row for row in batch
                    if row["organization_id"]
                ]
            }
        )

    cursor.close()
    conn.close()

    print(
        f"[SUCCESS] Loaded {total:,} Encounter nodes "
        "and their relationships"
    )
# --------------------------------------------------
# Load Conditions
# --------------------------------------------------

def load_conditions(graph):

    print("[INFO] Loading conditions from PostgreSQL...")

    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            patient_id,
            encounter_id,
            start_date,
            stop_date,
            code,
            description
        FROM synthea.conditions
    """)

    conditions = cursor.fetchall()

    print(f"[INFO] Found {len(conditions):,} conditions")

    rows = []

    for condition in conditions:

        (
            condition_id,
            patient_id,
            encounter_id,
            start_date,
            stop_date,
            code,
            description
        ) = condition

        rows.append({
            "id": str(condition_id),
            "patient_id": str(patient_id) if patient_id else None,
            "encounter_id": str(encounter_id) if encounter_id else None,
            "start_date": str(start_date) if start_date else None,
            "end_date": str(stop_date) if stop_date else None,
            "code": str(code) if code else None,
            "description": description
        })

    BATCH_SIZE = 500

    for start in range(0, len(rows), BATCH_SIZE):

        batch = rows[start:start + BATCH_SIZE]

        print(
            f"[INFO] Processing conditions "
            f"{start + 1:,}-{min(start + BATCH_SIZE, len(rows)):,}"
            f"/{len(rows):,}"
        )

        # Create Condition nodes
        graph.query(
            """
            UNWIND $rows AS row

            MERGE (c:Condition {id: row.id})

            SET
                c.start_date = row.start_date,
                c.end_date = row.stop_date,
                c.code = row.code,
                c.description = row.description
            """,
            {"rows": batch}
        )

        # Patient -> Condition
        graph.query(
            """
            UNWIND $rows AS row

            MATCH (p:Patient {id: row.patient_id})
            MATCH (c:Condition {id: row.id})

            MERGE (p)-[:HAS_CONDITION]->(c)
            """,
            {
                "rows": [
                    row for row in batch
                    if row["patient_id"]
                ]
            }
        )

        # Encounter -> Condition
        graph.query(
            """
            UNWIND $rows AS row

            MATCH (e:Encounter {id: row.encounter_id})
            MATCH (c:Condition {id: row.id})

            MERGE (e)-[:HAS_CONDITION]->(c)
            """,
            {
                "rows": [
                    row for row in batch
                    if row["encounter_id"]
                ]
            }
        )

    cursor.close()
    conn.close()

    print(
        f"[SUCCESS] Loaded {len(rows):,} Condition nodes "
        "and relationships"
    )
# --------------------------------------------------
# Load Procedures
# --------------------------------------------------

def load_procedures(graph):

    print("[INFO] Loading procedures from PostgreSQL...")

    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            start_time,
            stop_time,
            patient_id,
            encounter_id,
            code,
            description,
            base_cost,
            reason_code,
            reason_description
        FROM synthea.procedures
    """)

    procedures = cursor.fetchall()

    print(f"[INFO] Found {len(procedures):,} procedures")

    rows = []

    for procedure in procedures:

        (
            procedure_id,
            start_time,
            stop_time,
            patient_id,
            encounter_id,
            code,
            description,
            base_cost,
            reason_code,
            reason_description
        ) = procedure

        rows.append({
            "id": str(procedure_id),
            "start_time": str(start_time) if start_time else None,
            "stop_time": str(stop_time) if stop_time else None,
            "patient_id": str(patient_id) if patient_id else None,
            "encounter_id": str(encounter_id) if encounter_id else None,
            "code": str(code) if code else None,
            "description": description,
            "base_cost": base_cost,
            "reason_code": str(reason_code) if reason_code else None,
            "reason_description": reason_description
        })

    BATCH_SIZE = 500

    for start in range(0, len(rows), BATCH_SIZE):

        batch = rows[start:start + BATCH_SIZE]

        print(
            f"[INFO] Processing procedures "
            f"{start + 1:,}-{min(start + BATCH_SIZE, len(rows)):,}"
            f"/{len(rows):,}"
        )

        # Procedure nodes
        graph.query(
            """
            UNWIND $rows AS row

            MERGE (pr:Procedure {id: row.id})

            SET
                pr.start_time = row.start_time,
                pr.stop_time = row.stop_time,
                pr.code = row.code,
                pr.description = row.description,
                pr.base_cost = row.base_cost,
                pr.reason_code = row.reason_code,
                pr.reason_description = row.reason_description
            """,
            {"rows": batch}
        )

        # Patient -> Procedure
        graph.query(
            """
            UNWIND $rows AS row

            MATCH (p:Patient {id: row.patient_id})
            MATCH (pr:Procedure {id: row.id})

            MERGE (p)-[:UNDERWENT]->(pr)
            """,
            {
                "rows": [
                    row for row in batch
                    if row["patient_id"]
                ]
            }
        )

        # Procedure -> Encounter
        graph.query(
            """
            UNWIND $rows AS row

            MATCH (pr:Procedure {id: row.id})
            MATCH (e:Encounter {id: row.encounter_id})

            MERGE (pr)-[:DURING]->(e)
            """,
            {
                "rows": [
                    row for row in batch
                    if row["encounter_id"]
                ]
            }
        )

    cursor.close()
    conn.close()

    print(
        f"[SUCCESS] Loaded {len(rows):,} Procedure nodes "
        "and their relationships"
    )

# --------------------------------------------------
# Load Medications
# --------------------------------------------------

def load_medications(graph):

    print("[INFO] Loading medications from PostgreSQL...")

    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            start_time,
            stop_time,
            patient_id,
            payer_id,
            encounter_id,
            code,
            description,
            base_cost,
            payer_coverage,
            dispenses,
            total_cost,
            reason_code,
            reason_description
        FROM synthea.medications
    """)

    medications = cursor.fetchall()

    print(f"[INFO] Found {len(medications):,} medications")

    rows = []

    for medication in medications:

        (
            medication_id,
            start_time,
            stop_time,
            patient_id,
            payer_id,
            encounter_id,
            code,
            description,
            base_cost,
            payer_coverage,
            dispenses,
            total_cost,
            reason_code,
            reason_description
        ) = medication

        rows.append({
            "id": str(medication_id),
            "start_time": str(start_time) if start_time else None,
            "stop_time": str(stop_time) if stop_time else None,
            "patient_id": str(patient_id) if patient_id else None,
            "payer_id": str(payer_id) if payer_id else None,
            "encounter_id": str(encounter_id) if encounter_id else None,
            "code": str(code) if code else None,
            "description": description,
            "base_cost": base_cost,
            "payer_coverage": payer_coverage,
            "dispenses": dispenses,
            "total_cost": total_cost,
            "reason_code": str(reason_code) if reason_code else None,
            "reason_description": reason_description
        })

    BATCH_SIZE = 500

    for start in range(0, len(rows), BATCH_SIZE):

        batch = rows[start:start + BATCH_SIZE]

        print(
            f"[INFO] Processing medications "
            f"{start + 1:,}-{min(start + BATCH_SIZE, len(rows)):,}"
            f"/{len(rows):,}"
        )

        # --------------------------------------------------
        # Medication nodes
        # --------------------------------------------------

        graph.query(
            """
            UNWIND $rows AS row

            MERGE (m:Medication {id: row.id})

            SET
                m.start_time = row.start_time,
                m.stop_time = row.stop_time,
                m.code = row.code,
                m.description = row.description,
                m.base_cost = row.base_cost,
                m.payer_coverage = row.payer_coverage,
                m.dispenses = row.dispenses,
                m.total_cost = row.total_cost,
                m.reason_code = row.reason_code,
                m.reason_description = row.reason_description
            """,
            {"rows": batch}
        )

        # --------------------------------------------------
        # Patient -> Medication
        # --------------------------------------------------

        graph.query(
            """
            UNWIND $rows AS row

            MATCH (p:Patient {id: row.patient_id})
            MATCH (m:Medication {id: row.id})

            MERGE (p)-[:TAKES]->(m)
            """,
            {
                "rows": [
                    row for row in batch
                    if row["patient_id"]
                ]
            }
        )

        # --------------------------------------------------
        # Medication -> Encounter
        # --------------------------------------------------

        graph.query(
            """
            UNWIND $rows AS row

            MATCH (m:Medication {id: row.id})
            MATCH (e:Encounter {id: row.encounter_id})

            MERGE (m)-[:DURING]->(e)
            """,
            {
                "rows": [
                    row for row in batch
                    if row["encounter_id"]
                ]
            }
        )

    cursor.close()
    conn.close()

    print(
        f"[SUCCESS] Loaded {len(rows):,} Medication nodes "
        "and their relationships"
    )     
# --------------------------------------------------
# Load Observations
# --------------------------------------------------

def load_observations(graph):

    print("[INFO] Loading observations from PostgreSQL...")

    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            observation_date,
            patient_id,
            encounter_id,
            category,
            code,
            description,
            value,
            units,
            type
        FROM synthea.observations
    """)

    observations = cursor.fetchall()

    print(f"[INFO] Found {len(observations):,} observations")

    rows = []

    for observation in observations:

        (
            observation_id,
            observation_date,
            patient_id,
            encounter_id,
            category,
            code,
            description,
            value,
            units,
            obs_type
        ) = observation

        rows.append({
            "id": str(observation_id),
            "observation_date": str(observation_date) if observation_date else None,
            "patient_id": str(patient_id) if patient_id else None,
            "encounter_id": str(encounter_id) if encounter_id else None,
            "category": category,
            "code": str(code) if code else None,
            "description": description,
            "value": value,
            "units": units,
            "type": obs_type
        })

    BATCH_SIZE = 2000

    total = len(rows)

    for start in range(0, total, BATCH_SIZE):

        batch = rows[start:start + BATCH_SIZE]

        print(
            f"[INFO] Processing observations "
            f"{start + 1:,}-{min(start + BATCH_SIZE, total):,}"
            f"/{total:,}"
        )

        # Observation nodes
        graph.query(
            """
            UNWIND $rows AS row

            MERGE (o:Observation {id: row.id})

            SET
                o.observation_date = row.observation_date,
                o.category = row.category,
                o.code = row.code,
                o.description = row.description,
                o.value = row.value,
                o.units = row.units,
                o.type = row.type
            """,
            {"rows": batch}
        )

        # Patient -> Observation
        graph.query(
            """
            UNWIND $rows AS row

            MATCH (p:Patient {id: row.patient_id})
            MATCH (o:Observation {id: row.id})

            MERGE (p)-[:HAS_OBSERVATION]->(o)
            """,
            {
                "rows": [
                    row for row in batch
                    if row["patient_id"]
                ]
            }
        )

        # Encounter -> Observation
        graph.query(
            """
            UNWIND $rows AS row

            MATCH (e:Encounter {id: row.encounter_id})
            MATCH (o:Observation {id: row.id})

            MERGE (e)-[:HAS_OBSERVATION]->(o)
            """,
            {
                "rows": [
                    row for row in batch
                    if row["encounter_id"]
                ]
            }
        )

    cursor.close()
    conn.close()

    print(
        f"[SUCCESS] Loaded {total:,} Observation nodes "
        "and relationships"
    )

# --------------------------------------------------
# Load Allergies
# --------------------------------------------------

def load_allergies(graph):

    print("[INFO] Loading allergies from PostgreSQL...")

    conn = get_postgres_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            start_date,
            stop_date,
            patient_id,
            encounter_id,
            code,
            system,
            description,
            allergy_type,
            category,
            reaction1,
            description1,
            severity1,
            reaction2,
            description2,
            severity2
        FROM synthea.allergies
    """)

    allergies = cursor.fetchall()

    print(f"[INFO] Found {len(allergies):,} allergies")

    rows = []

    for allergy in allergies:

        (
            allergy_id,
            start_date,
            stop_date,
            patient_id,
            encounter_id,
            code,
            system,
            description,
            allergy_type,
            category,
            reaction1,
            description1,
            severity1,
            reaction2,
            description2,
            severity2
        ) = allergy

        rows.append({
            "id": str(allergy_id),
            "start_date": str(start_date) if start_date else None,
            "stop_date": str(stop_date) if stop_date else None,
            "patient_id": str(patient_id) if patient_id else None,
            "encounter_id": str(encounter_id) if encounter_id else None,
            "code": str(code) if code else None,
            "system": system,
            "description": description,
            "allergy_type": allergy_type,
            "category": category,
            "reaction1": reaction1,
            "description1": description1,
            "severity1": severity1,
            "reaction2": reaction2,
            "description2": description2,
            "severity2": severity2
        })

    BATCH_SIZE = 500

    total = len(rows)

    for start in range(0, total, BATCH_SIZE):

        batch = rows[start:start + BATCH_SIZE]

        print(
            f"[INFO] Processing allergies "
            f"{start + 1:,}-{min(start + BATCH_SIZE, total):,}"
            f"/{total:,}"
        )

        # Allergy nodes
        graph.query(
            """
            UNWIND $rows AS row

            MERGE (a:Allergy {id: row.id})

            SET
                a.start_date = row.start_date,
                a.stop_date = row.stop_date,
                a.code = row.code,
                a.system = row.system,
                a.description = row.description,
                a.allergy_type = row.allergy_type,
                a.category = row.category,
                a.reaction1 = row.reaction1,
                a.description1 = row.description1,
                a.severity1 = row.severity1,
                a.reaction2 = row.reaction2,
                a.description2 = row.description2,
                a.severity2 = row.severity2
            """,
            {"rows": batch}
        )

        # Patient -> Allergy
        graph.query(
            """
            UNWIND $rows AS row

            MATCH (p:Patient {id: row.patient_id})
            MATCH (a:Allergy {id: row.id})

            MERGE (p)-[:HAS_ALLERGY]->(a)
            """,
            {
                "rows": [
                    row for row in batch
                    if row["patient_id"]
                ]
            }
        )

        # Encounter -> Allergy
        graph.query(
            """
            UNWIND $rows AS row

            MATCH (e:Encounter {id: row.encounter_id})
            MATCH (a:Allergy {id: row.id})

            MERGE (e)-[:HAS_ALLERGY]->(a)
            """,
            {
                "rows": [
                    row for row in batch
                    if row["encounter_id"]
                ]
            }
        )

    cursor.close()
    conn.close()

    print(
        f"[SUCCESS] Loaded {total:,} Allergy nodes "
        "and relationships"
    )

# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("MedGraph AI - Synthea Knowledge Graph Loader")
    print("=" * 60)

    graph = get_falkor_graph()

    load_patients(graph)
    load_organizations(graph)
    load_providers(graph)
    load_encounters(graph)
    load_conditions(graph)
    load_procedures(graph)
    load_medications(graph)
    load_observations(graph)
    load_allergies(graph)

    print("\n" + "=" * 60)
    print("SUCCESS: Synthea Knowledge Graph loading completed!")
    print("=" * 60)