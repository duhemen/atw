"""Konfigurasi global ATW."""
from pathlib import Path
from pydantic_settings import BaseSettings
from sqlalchemy.engine import URL
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    APP_NAME: str = "ATW - Anggaran Transparency Watch"
    APP_VERSION: str = "0.1.0"

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_PUBLIC: str = "atw_public"
    DB_INTERNAL: str = "atw_internal"

    @property
    def PUBLIC_DB_URL(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_PUBLIC,
        )

    @property
    def INTERNAL_DB_URL(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_INTERNAL,
        )

    GEO_DIR: Path = DATA_DIR / "geo"
    BOUNDARIES_DIR: Path = GEO_DIR / "boundaries"
    PROJECTS_DIR: Path = GEO_DIR / "projects"

    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    SECRET_KEY: str = "change-me-in-production"

    FVI_DEFAULT_YEAR: int = 2024
    FVI_MIN_HISTORY_YEARS: int = 3
    MONTE_CARLO_RUNS: int = 10_000

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()