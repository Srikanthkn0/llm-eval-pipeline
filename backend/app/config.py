import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

_data_dir = os.getenv("DATA_DIR", "")
DATA_DIR = Path(_data_dir) if _data_dir else BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "eval_pipeline.db"


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


settings = Settings()

DATA_DIR.mkdir(parents=True, exist_ok=True)