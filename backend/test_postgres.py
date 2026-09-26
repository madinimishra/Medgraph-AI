import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

host = os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("POSTGRES_PORT", "5432")
database = os.getenv("POSTGRES_DB", "medgraph")
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD")

url = (
    f"postgresql+psycopg2://"
    f"{user}:{password}@{host}:{port}/{database}"
)

try:
    engine = create_engine(url)

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), version();")
        )

        database_name, version = result.fetchone()

        print("[SUCCESS] PostgreSQL connected!")
        print(f"[INFO] Database: {database_name}")
        print(f"[INFO] Version: {version}")

except Exception as e:
    print("[ERROR] PostgreSQL connection failed!")
    print(e)