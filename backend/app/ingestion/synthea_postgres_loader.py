import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "synthea"

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "medgraph")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# --------------------------------------------------
# Patients
# --------------------------------------------------

def load_patients():
    csv_path = DATA_DIR / "patients.csv"

    print("[INFO] Loading patients.csv")

    df = pd.read_csv(csv_path)

    print(f"[INFO] Found {len(df):,} patient records")

    patients = pd.DataFrame({
        "id": df["Id"],
        "birthdate": pd.to_datetime(
            df["BIRTHDATE"],
            errors="coerce"
        ).dt.date,

        "deathdate": pd.to_datetime(
            df["DEATHDATE"],
            errors="coerce"
        ).dt.date,

        "ssn": df["SSN"],
        "drivers": df["DRIVERS"],
        "passport": df["PASSPORT"],
        "prefix": df["PREFIX"],

        "first_name": df["FIRST"],
        "last_name": df["LAST"],
        "suffix": df["SUFFIX"],
        "maiden_name": df["MAIDEN"],

        "marital_status": df["MARITAL"],
        "race": df["RACE"],
        "ethnicity": df["ETHNICITY"],
        "gender": df["GENDER"],
        "birthplace": df["BIRTHPLACE"],

        "address": df["ADDRESS"],
        "city": df["CITY"],
        "state": df["STATE"],
        "county": df["COUNTY"],
        "zip": df["ZIP"].astype("string"),

        "latitude": pd.to_numeric(
            df["LAT"],
            errors="coerce"
        ),

        "longitude": pd.to_numeric(
            df["LON"],
            errors="coerce"
        ),

        "healthcare_expenses": pd.to_numeric(
            df["HEALTHCARE_EXPENSES"],
            errors="coerce"
        ),

        "healthcare_coverage": pd.to_numeric(
            df["HEALTHCARE_COVERAGE"],
            errors="coerce"
        ),
    })

    # Replace pandas NaN/NaT with None
    patients = patients.where(
        pd.notnull(patients),
        None
    )

    print("[INFO] Inserting patients into PostgreSQL...")

    patients.to_sql(
        "patients",
        engine,
        schema="synthea",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )

    print(
        f"[SUCCESS] Loaded {len(patients):,} patients"
    )
def load_organizations():
    csv_path = DATA_DIR / "organizations.csv"

    print("[INFO] Loading organizations.csv")

    df = pd.read_csv(csv_path)

    organizations = pd.DataFrame({
        "id": df["Id"],
        "name": df["NAME"],
        "address": df["ADDRESS"],
        "city": df["CITY"],
        "state": df["STATE"],
        "zip": df["ZIP"].astype("string"),
        "latitude": pd.to_numeric(df["LAT"], errors="coerce"),
        "longitude": pd.to_numeric(df["LON"], errors="coerce"),
        "phone": df["PHONE"],
        "revenue": pd.to_numeric(
            df["REVENUE"],
            errors="coerce"
        ),
        "utilization": pd.to_numeric(
            df["UTILIZATION"],
            errors="coerce"
        ),
    })

    organizations = organizations.where(
        pd.notnull(organizations),
        None
    )

    organizations.to_sql(
        "organizations",
        engine,
        schema="synthea",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )

    print(
        f"[SUCCESS] Loaded {len(organizations):,} organizations"
    )
def load_providers():
    csv_path = DATA_DIR / "providers.csv"

    print("[INFO] Loading providers.csv")

    df = pd.read_csv(csv_path)

    providers = pd.DataFrame({
        "id": df["Id"],
        "organization_id": df["ORGANIZATION"],
        "name": df["NAME"],
        "gender": df["GENDER"],
        "speciality": df["SPECIALITY"],
        "address": df["ADDRESS"],
        "city": df["CITY"],
        "state": df["STATE"],
        "zip": df["ZIP"].astype("string"),
        "latitude": pd.to_numeric(
            df["LAT"],
            errors="coerce"
        ),
        "longitude": pd.to_numeric(
            df["LON"],
            errors="coerce"
        ),
        "utilization": pd.to_numeric(
            df["UTILIZATION"],
            errors="coerce"
        ),
    })

    providers = providers.where(
        pd.notnull(providers),
        None
    )

    providers.to_sql(
        "providers",
        engine,
        schema="synthea",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )

    print(
        f"[SUCCESS] Loaded {len(providers):,} providers"
    )
def load_encounters():
    csv_path = DATA_DIR / "encounters.csv"

    print("[INFO] Loading encounters.csv")

    df = pd.read_csv(csv_path)

    encounters = pd.DataFrame({
        "id": df["Id"],

        "start_time": pd.to_datetime(
            df["START"],
            errors="coerce",
            utc=True
        ),

        "stop_time": pd.to_datetime(
            df["STOP"],
            errors="coerce",
            utc=True
        ),

        "patient_id": df["PATIENT"],
        "organization_id": df["ORGANIZATION"],
        "provider_id": df["PROVIDER"],
        "payer_id": df["PAYER"],

        "encounter_class": df["ENCOUNTERCLASS"],

        "code": df["CODE"].astype("string"),

        "description": df["DESCRIPTION"],

        "base_encounter_cost": pd.to_numeric(
            df["BASE_ENCOUNTER_COST"],
            errors="coerce"
        ),

        "total_claim_cost": pd.to_numeric(
            df["TOTAL_CLAIM_COST"],
            errors="coerce"
        ),

        "payer_coverage": pd.to_numeric(
            df["PAYER_COVERAGE"],
            errors="coerce"
        ),

        "reason_code": df["REASONCODE"].astype("string"),

        "reason_description": df["REASONDESCRIPTION"],
    })

    encounters = encounters.where(
        pd.notnull(encounters),
        None
    )

    print(
        f"[INFO] Inserting {len(encounters):,} encounters..."
    )

    encounters.to_sql(
        "encounters",
        engine,
        schema="synthea",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    print(
        f"[SUCCESS] Loaded {len(encounters):,} encounters"
    )
def load_conditions():
    csv_path = DATA_DIR / "conditions.csv"

    print("[INFO] Loading conditions.csv")

    df = pd.read_csv(csv_path)

    print(f"[INFO] Found {len(df):,} condition records")

    conditions = pd.DataFrame({
        "start_date": pd.to_datetime(
            df["START"],
            errors="coerce"
        ).dt.date,

        "stop_date": pd.to_datetime(
            df["STOP"],
            errors="coerce"
        ).dt.date,

        "patient_id": df["PATIENT"],
        "encounter_id": df["ENCOUNTER"],
        "code": df["CODE"].astype("string"),
        "description": df["DESCRIPTION"],
    })

    conditions = conditions.where(
        pd.notnull(conditions),
        None
    )

    print(
        f"[INFO] Inserting {len(conditions):,} conditions..."
    )

    conditions.to_sql(
        "conditions",
        engine,
        schema="synthea",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    print(
        f"[SUCCESS] Loaded {len(conditions):,} conditions"
    )
def load_medications():
    csv_path = DATA_DIR / "medications.csv"

    print("[INFO] Loading medications.csv")

    df = pd.read_csv(csv_path)

    print(f"[INFO] Found {len(df):,} medication records")

    medications = pd.DataFrame({
        "start_time": pd.to_datetime(
            df["START"],
            errors="coerce",
            utc=True
        ),

        "stop_time": pd.to_datetime(
            df["STOP"],
            errors="coerce",
            utc=True
        ),

        "patient_id": df["PATIENT"],
        "payer_id": df["PAYER"],
        "encounter_id": df["ENCOUNTER"],

        "code": df["CODE"].astype("string"),

        "description": df["DESCRIPTION"],

        "base_cost": pd.to_numeric(
            df["BASE_COST"],
            errors="coerce"
        ),

        "payer_coverage": pd.to_numeric(
            df["PAYER_COVERAGE"],
            errors="coerce"
        ),

        "dispenses": pd.to_numeric(
            df["DISPENSES"],
            errors="coerce"
        ),

        "total_cost": pd.to_numeric(
            df["TOTALCOST"],
            errors="coerce"
        ),

        "reason_code": df["REASONCODE"].astype("string"),

        "reason_description": df["REASONDESCRIPTION"],
    })

    medications = medications.where(
        pd.notnull(medications),
        None
    )

    print(
        f"[INFO] Inserting {len(medications):,} medications..."
    )

    medications.to_sql(
        "medications",
        engine,
        schema="synthea",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    print(
        f"[SUCCESS] Loaded {len(medications):,} medications"
    )
def load_observations():
    csv_path = DATA_DIR / "observations.csv"

    print("[INFO] Loading observations.csv")

    df = pd.read_csv(csv_path)

    print(
        f"[INFO] Found {len(df):,} observation records"
    )

    observations = pd.DataFrame({
        "observation_date": pd.to_datetime(
            df["DATE"],
            errors="coerce",
            utc=True
        ),

        "patient_id": df["PATIENT"],
        "encounter_id": df["ENCOUNTER"],

        "category": df["CATEGORY"],

        "code": df["CODE"].astype("string"),

        "description": df["DESCRIPTION"],

        "value": df["VALUE"].astype("string"),

        "units": df["UNITS"].astype("string"),

        "type": df["TYPE"],
    })

    observations = observations.where(
        pd.notnull(observations),
        None
    )

    print(
        "[INFO] Inserting observations in batches..."
    )

    observations.to_sql(
        "observations",
        engine,
        schema="synthea",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=2000,
    )

    print(
        f"[SUCCESS] Loaded {len(observations):,} observations"
    )
def load_procedures():
    csv_path = DATA_DIR / "procedures.csv"

    print("[INFO] Loading procedures.csv")

    df = pd.read_csv(csv_path)

    print(f"[INFO] Found {len(df):,} procedure records")

    procedures = pd.DataFrame({
        "start_time": pd.to_datetime(
            df["START"],
            errors="coerce",
            utc=True
        ),

        "stop_time": pd.to_datetime(
            df["STOP"],
            errors="coerce",
            utc=True
        ),

        "patient_id": df["PATIENT"],
        "encounter_id": df["ENCOUNTER"],

        "code": df["CODE"].astype("string"),

        "description": df["DESCRIPTION"],

        "base_cost": pd.to_numeric(
            df["BASE_COST"],
            errors="coerce"
        ),

        "reason_code": df["REASONCODE"].astype("string"),

        "reason_description": df["REASONDESCRIPTION"],
    })

    procedures = procedures.where(
        pd.notnull(procedures),
        None
    )

    print(
        f"[INFO] Inserting {len(procedures):,} procedures..."
    )

    procedures.to_sql(
        "procedures",
        engine,
        schema="synthea",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=2000,
    )

    print(
        f"[SUCCESS] Loaded {len(procedures):,} procedures"
    )
def load_allergies():
    csv_path = DATA_DIR / "allergies.csv"

    print("[INFO] Loading allergies.csv")

    df = pd.read_csv(csv_path)

    print(f"[INFO] Found {len(df):,} allergy records")

    allergies = pd.DataFrame({
        "start_date": pd.to_datetime(
            df["START"],
            errors="coerce"
        ).dt.date,

        "stop_date": pd.to_datetime(
            df["STOP"],
            errors="coerce"
        ).dt.date,

        "patient_id": df["PATIENT"],
        "encounter_id": df["ENCOUNTER"],

        "code": df["CODE"].astype("string"),

        "system": df["SYSTEM"],
        "description": df["DESCRIPTION"],
        "allergy_type": df["TYPE"],
        "category": df["CATEGORY"],

        "reaction1": df["REACTION1"].astype("string"),
        "description1": df["DESCRIPTION1"],
        "severity1": df["SEVERITY1"],

        "reaction2": df["REACTION2"].astype("string"),
        "description2": df["DESCRIPTION2"],
        "severity2": df["SEVERITY2"],
    })

    allergies = allergies.where(
        pd.notnull(allergies),
        None
    )

    print(
        f"[INFO] Inserting {len(allergies):,} allergies..."
    )

    allergies.to_sql(
        "allergies",
        engine,
        schema="synthea",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    print(
        f"[SUCCESS] Loaded {len(allergies):,} allergies"
    )
# --------------------------------------------------
# Main
# --------------------------------------------------

if __name__ == "__main__":
    
   
     load_allergies()