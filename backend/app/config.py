import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

_data_dir = os.getenv("DATA_DIR", "")
DATA_DIR = Path(_data_dir) if _data_dir else BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "eval_pipeline.db"
DATABASE_URL = os.getenv("DATABASE_URL", "")


def _parse_origins(raw: str) -> list[str]:
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "LLM Eval Pipeline API")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    FRONTEND_ORIGINS: list[str] = _parse_origins(
        os.getenv(
            "FRONTEND_ORIGINS",
            os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
        )
    )
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ALLOW_MOCK_MODEL: bool = os.getenv("ALLOW_MOCK_MODEL", "").lower() in {
        "1",
        "true",
        "yes",
    }
    LLM_REQUEST_TIMEOUT_SEC: int = int(os.getenv("LLM_REQUEST_TIMEOUT_SEC", "60"))
    LLM_MAX_RETRIES: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
    MAX_UPLOAD_BYTES: int = int(os.getenv("MAX_UPLOAD_BYTES", str(2 * 1024 * 1024)))
    STALE_JOB_MINUTES: int = int(os.getenv("STALE_JOB_MINUTES", "30"))
    API_KEY: str = os.getenv("API_KEY", "")
    REQUIRE_API_KEY: bool = os.getenv("REQUIRE_API_KEY", "").lower() in {"1", "true", "yes"}
    RATE_LIMIT_PER_MIN: int = int(os.getenv("RATE_LIMIT_PER_MIN", "120"))
    RATE_LIMIT_EVALS_PER_MIN: int = int(os.getenv("RATE_LIMIT_EVALS_PER_MIN", "10"))
    RATE_LIMIT_SCAN_PER_MIN: int = int(os.getenv("RATE_LIMIT_SCAN_PER_MIN", "30"))
    MAX_EVAL_ROWS: int = int(os.getenv("MAX_EVAL_ROWS", "500"))
    MAX_PROMPT_CHARS: int = int(os.getenv("MAX_PROMPT_CHARS", "8000"))
    MAX_CONCURRENT_JOBS: int = int(os.getenv("MAX_CONCURRENT_JOBS", "3"))
    ML_GUARD_ENABLED: bool = os.getenv("ML_GUARD_ENABLED", "true").lower() in {
        "1",
        "true",
        "yes",
    }
    ML_GUARD_BACKEND: str = os.getenv("ML_GUARD_BACKEND", "sklearn")
    ML_GUARD_THRESHOLD: float = float(os.getenv("ML_GUARD_THRESHOLD", "0.60"))
    ML_GUARD_WARN_THRESHOLD: float = float(os.getenv("ML_GUARD_WARN_THRESHOLD", "0.45"))
    ML_GUARD_MODEL_PATH: Path = Path(
        os.getenv(
            "ML_GUARD_MODEL_PATH",
            str(BASE_DIR / "data" / "models" / "injection_classifier.joblib"),
        )
    )

    @property
    def require_api_key(self) -> bool:
        if self.REQUIRE_API_KEY:
            return True
        return self.is_production and bool(self.API_KEY)

    @property
    def use_postgres(self) -> bool:
        return DATABASE_URL.startswith(("postgres://", "postgresql://"))

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def has_llm_key(self) -> bool:
        return bool(self.GEMINI_API_KEY or self.GROQ_API_KEY or self.OPENAI_API_KEY)

    @property
    def mock_allowed(self) -> bool:
        # Dev always; prod if ALLOW_MOCK_MODEL or no API keys configured.
        if self.ALLOW_MOCK_MODEL or not self.is_production:
            return True
        return not self.has_llm_key


settings = Settings()

DATA_DIR.mkdir(parents=True, exist_ok=True)