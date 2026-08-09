from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://beyondtheveil:beyondtheveil@localhost:5432/beyondtheveil"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24
    veil_duration_seconds: int = 5 * 60
    # Comma-separated list of origins allowed to call this API (CORS). Set
    # this to the deployed frontend's URL(s) in production - the localhost
    # default is dev-only.
    frontend_origin: str = "http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]


settings = Settings()
