import psycopg2


DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "medgraph",
    "user": "postgres",
    "password": "postgres123",
}


def main():
    print("[INFO] Connecting to PostgreSQL...")

    conn = psycopg2.connect(**DB_CONFIG)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM synthea.patients;
    """)

    patient_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM synthea.conditions;
    """)

    condition_count = cursor.fetchone()[0]

    print("[SUCCESS] PostgreSQL connected!")
    print("[INFO] Database: medgraph")
    print("[INFO] Synthea patients:", patient_count)
    print("[INFO] Synthea conditions:", condition_count)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()