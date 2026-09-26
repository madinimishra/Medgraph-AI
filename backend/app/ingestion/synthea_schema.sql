CREATE TABLE IF NOT EXISTS synthea.patients (
    id UUID PRIMARY KEY,
    birthdate DATE,
    deathdate DATE,
    ssn VARCHAR(20),
    drivers VARCHAR(50),
    passport VARCHAR(50),
    prefix VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    suffix VARCHAR(20),
    maiden_name VARCHAR(100),
    marital_status VARCHAR(20),
    race VARCHAR(100),
    ethnicity VARCHAR(100),
    gender VARCHAR(20),
    birthplace TEXT,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    county VARCHAR(100),
    zip VARCHAR(20),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    healthcare_expenses NUMERIC(15,2),
    healthcare_coverage NUMERIC(15,2)
);

CREATE TABLE IF NOT EXISTS synthea.organizations (
    id UUID PRIMARY KEY,
    name TEXT,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    zip VARCHAR(20),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    phone VARCHAR(30),
    revenue NUMERIC(15,2),
    utilization INTEGER
);

CREATE TABLE IF NOT EXISTS synthea.providers (
    id UUID PRIMARY KEY,
    organization_id UUID,
    name TEXT,
    gender VARCHAR(20),
    speciality VARCHAR(150),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    zip VARCHAR(20),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    utilization INTEGER
);

CREATE TABLE IF NOT EXISTS synthea.encounters (
    id UUID PRIMARY KEY,
    start_time TIMESTAMPTZ,
    stop_time TIMESTAMPTZ,
    patient_id UUID,
    organization_id UUID,
    provider_id UUID,
    payer_id UUID,
    encounter_class VARCHAR(100),
    code VARCHAR(50),
    description TEXT,
    base_encounter_cost NUMERIC(15,2),
    total_claim_cost NUMERIC(15,2),
    payer_coverage NUMERIC(15,2),
    reason_code VARCHAR(100),
    reason_description TEXT
);

CREATE TABLE IF NOT EXISTS synthea.conditions (
    id BIGSERIAL PRIMARY KEY,
    start_date DATE,
    stop_date DATE,
    patient_id UUID,
    encounter_id UUID,
    code VARCHAR(100),
    description TEXT
);

CREATE TABLE IF NOT EXISTS synthea.medications (
    id BIGSERIAL PRIMARY KEY,
    start_time TIMESTAMPTZ,
    stop_time TIMESTAMPTZ,
    patient_id UUID,
    payer_id UUID,
    encounter_id UUID,
    code VARCHAR(100),
    description TEXT,
    base_cost NUMERIC(15,2),
    payer_coverage NUMERIC(15,2),
    dispenses INTEGER,
    total_cost NUMERIC(15,2),
    reason_code VARCHAR(100),
    reason_description TEXT
);

CREATE TABLE IF NOT EXISTS synthea.observations (
    id BIGSERIAL PRIMARY KEY,
    observation_date TIMESTAMPTZ,
    patient_id UUID,
    encounter_id UUID,
    category VARCHAR(100),
    code VARCHAR(100),
    description TEXT,
    value TEXT,
    units VARCHAR(50),
    type VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS synthea.procedures (
    id BIGSERIAL PRIMARY KEY,
    start_time TIMESTAMPTZ,
    stop_time TIMESTAMPTZ,
    patient_id UUID,
    encounter_id UUID,
    code VARCHAR(100),
    description TEXT,
    base_cost NUMERIC(15,2),
    reason_code VARCHAR(100),
    reason_description TEXT
);

CREATE TABLE IF NOT EXISTS synthea.allergies (
    id BIGSERIAL PRIMARY KEY,
    start_date DATE,
    stop_date DATE,
    patient_id UUID,
    encounter_id UUID,
    code VARCHAR(100),
    system VARCHAR(100),
    description TEXT,
    allergy_type VARCHAR(100),
    category VARCHAR(100),
    reaction1 VARCHAR(100),
    description1 TEXT,
    severity1 VARCHAR(50),
    reaction2 VARCHAR(100),
    description2 TEXT,
    severity2 VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS synthea.careplans (
    id UUID PRIMARY KEY,
    start_date DATE,
    stop_date DATE,
    patient_id UUID,
    encounter_id UUID,
    code VARCHAR(100),
    description TEXT,
    reason_code VARCHAR(100),
    reason_description TEXT
);

CREATE TABLE IF NOT EXISTS synthea.immunizations (
    id BIGSERIAL PRIMARY KEY,
    immunization_date TIMESTAMPTZ,
    patient_id UUID,
    encounter_id UUID,
    code VARCHAR(100),
    description TEXT,
    base_cost NUMERIC(15,2)
);