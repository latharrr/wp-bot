from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core API
    api_key: str = "change-me-api-key"
    jwt_secret: str = "change-me-jwt-secret"
    jwt_expiry_hours: int = 24
    # Comma-separated dashboard origins allowed to call the API cross-origin. The wildcard
    # default is fine for local dev (dashboard on localhost:3000, API on localhost:8000); set
    # this explicitly in production so a JWT stolen via some other means can't be replayed from
    # an arbitrary third-party page (the JWT lives in localStorage, not a cookie, so this isn't
    # exploitable today, but a wildcard is still a needless hardening gap to leave open).
    cors_allowed_origins: str = "*"

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_poll_history_rpc: str = "get_poll_user_history"

    # WhatsApp bridge
    whatsapp_bridge_enabled: bool = True
    whatsapp_internal_token: str = "change-me-internal-token"
    whatsapp_internal_base_url: str = "http://127.0.0.1:8000"
    whatsapp_bridge_control_url: str = "http://127.0.0.1:8801"
    whatsapp_bridge_control_token: str = "change-me-control-token"
    # QR-code linking is the reliable path (verified against a live connection); pairing-code
    # linking has been unreliable against WhatsApp's current servers -- see bridge_process.py.
    whatsapp_use_pairing_code: bool = False
    whatsapp_phone_number: str = ""
    baileys_project_dir: str = "whatsapp_bridge"
    baileys_auth_dir: str = "whatsapp_bridge/baileys_auth_info"
    baileys_log_level: str = "info"
    baileys_log_dir: str = "whatsapp_bridge/logs"

    # SMTP alerts
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    whatsapp_alert_recipients: str = ""

    @property
    def cors_allowed_origin_list(self) -> list[str]:
        if self.cors_allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def alert_recipient_list(self) -> list[str]:
        return [addr.strip() for addr in self.whatsapp_alert_recipients.split(",") if addr.strip()]

    @property
    def baileys_project_path(self) -> Path:
        return Path(self.baileys_project_dir).resolve()

    @property
    def baileys_log_path(self) -> Path:
        return Path(self.baileys_log_dir).resolve()

    def insecure_defaults_still_in_use(self) -> list[str]:
        """Names of secrets still at their .env.example placeholder value. Anyone who forgets
        to change JWT_SECRET in particular can be trivially impersonated as any user, since the
        placeholder is public (it's committed in this repo) -- refuse to boot rather than run
        with a well-known signing key."""
        defaults = {
            "API_KEY": ("change-me-api-key", self.api_key),
            "JWT_SECRET": ("change-me-jwt-secret", self.jwt_secret),
            "WHATSAPP_INTERNAL_TOKEN": ("change-me-internal-token", self.whatsapp_internal_token),
            "WHATSAPP_BRIDGE_CONTROL_TOKEN": ("change-me-control-token", self.whatsapp_bridge_control_token),
        }
        return [name for name, (placeholder, actual) in defaults.items() if actual == placeholder]


@lru_cache
def get_settings() -> Settings:
    return Settings()
