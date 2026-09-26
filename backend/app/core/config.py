from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    FALKOR_HOST: str
    FALKOR_PORT: int
    FALKOR_GRAPH: str
    FALKOR_SYNTHEA_GRAPH: str = "medgraph_synthea"

    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "models/gemini-3.6-flash"
    GEMINI_MODEL_FALLBACKS: str = "models/gemini-flash-lite-latest"

    # LLM_PROVIDER selects the backend generate_content() (core/llm_client.py)
    # actually talks to: "gemini" (default, public API) or "ollama" (a
    # locally-run model - no data leaves the machine). See
    # docs/PATH_TO_PRODUCTION.md for why this matters for real patient data.
    LLM_PROVIDER: str = "gemini"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHROMA_PERSIST_DIR: str = "chroma_db"
    CHROMA_COLLECTION: str = "clinical_documents"

    DEFAULT_HOSPITAL_NAME: str = "MedGraph Super Speciality Hospital"
    UPLOAD_DIR: str = "app/uploads"

    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()