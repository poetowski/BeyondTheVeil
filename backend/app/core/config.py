from dataclasses import dataclass
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass(frozen=True)
class _GameplayPacing:
    """Gameplay-pacing constants that differ between real play and manual
    testing. Bundled together so there's exactly one dial (Settings.app_env)
    instead of independent env vars for each constant that could drift out
    of sync with each other."""

    veil_duration_seconds: int
    hp_regen_seconds_to_full: int


# Add new pacing constants here (and to _GameplayPacing above), not as their
# own Settings fields - app_env should stay the single source of truth for
# every value that needs a fast "test" variant.
_PACING_PRESETS: dict[str, _GameplayPacing] = {
    "prod": _GameplayPacing(veil_duration_seconds=5 * 60, hp_regen_seconds_to_full=120 * 60),
    "test": _GameplayPacing(veil_duration_seconds=10, hp_regen_seconds_to_full=2 * 60),
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://beyondtheveil:beyondtheveil@localhost:5432/beyondtheveil"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24
    # Single switch for every gameplay-pacing constant (see _PACING_PRESETS
    # above). "prod" is the safe default - set APP_ENV=test to opt into
    # fast manual-testing values.
    app_env: Literal["prod", "test"] = "prod"
    # Comma-separated list of origins allowed to call this API (CORS). Set
    # this to the deployed frontend's URL(s) in production - the localhost
    # default is dev-only.
    frontend_origin: str = "http://localhost:5173"

    @property
    def _pacing(self) -> _GameplayPacing:
        return _PACING_PRESETS[self.app_env]

    @property
    def veil_duration_seconds(self) -> int:
        return self._pacing.veil_duration_seconds

    @property
    def hp_regen_seconds_to_full(self) -> int:
        return self._pacing.hp_regen_seconds_to_full

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origin.split(",") if origin.strip()]


settings = Settings()
