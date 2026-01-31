from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    api_title: str = os.getenv("API_TITLE", "Learning Hub API")
    api_version: str = os.getenv("API_VERSION", "0.1.0")
    courses_csv: str = os.getenv("COURSES_CSV", "courses.csv")
    db_path: str = os.getenv("DATABASE_PATH", "learning_hub.db")


settings = Settings()
