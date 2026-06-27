import os
from pathlib import Path

import pytest

os.environ["DATA_DIR"] = str(Path(__file__).resolve().parent / "tmp_data")
os.environ["FRONTEND_ORIGINS"] = "http://localhost:5173"
os.environ["APP_ENV"] = "development"
os.environ["ALLOW_MOCK_MODEL"] = "true"

from app.database import init_db  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_database():
    data_dir = Path(os.environ["DATA_DIR"])
    db_path = data_dir / "eval_pipeline.db"
    if db_path.exists():
        db_path.unlink()
    data_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    yield
    if db_path.exists():
        db_path.unlink()