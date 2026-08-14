from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    openai_api_key: str = ""
    crop_health_api_key: str = ""
    tavily_api_key: str = ""  # web-search fallback for when the KB has nothing — optional
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-5.6-sol"
    monitor_interval_hours: float = 0.05  # 3 minutes — TEMP for testing, revert to 6
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    bdapps_application_id: str = ""
    bdapps_password: str = ""
    bdapps_base_url: str = "https://developer.bdapps.com"
    bdapps_sms_source_address: str = ""
    bdapps_sms_keyword: str = "agrobot"
    bdapps_api_version: str = "1.0"
    fixie_url: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        # Some managed Postgres providers (e.g. Neon) hand out the legacy
        # "postgres://" scheme, which SQLAlchemy's psycopg2 driver rejects.
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
