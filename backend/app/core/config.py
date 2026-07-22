"""Configuration centrale de l'application (chargée depuis l'environnement)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Environnement
    api_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Base de données
    database_url: str = "postgresql+psycopg://washmanager:change-me@db:5432/washmanager"

    # Sécurité
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 720
    jwt_algorithm: str = "HS256"
    # Clé partagée signant les événements envoyés par le pipeline `ai/`
    ai_ingest_api_key: str = "change-me-ingest-key"

    # Stockage médias
    media_root: str = "/data/media"
    media_base_url: str = "http://localhost:8000/media"

    # Notifications
    whatsapp_api_url: str = ""
    whatsapp_api_token: str = ""
    whatsapp_manager_numbers: str = ""  # séparés par virgule
    # Email (SMTP) — TODO(dev): renseigner pour activer le canal email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "wash-manager@example.com"
    alert_emails: str = ""              # destinataires email, séparés par virgule
    report_daily_hour: int = 21

    @property
    def manager_numbers(self) -> list[str]:
        return [n.strip() for n in self.whatsapp_manager_numbers.split(",") if n.strip()]

    @property
    def emails_alerte(self) -> list[str]:
        return [e.strip() for e in self.alert_emails.split(",") if e.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
