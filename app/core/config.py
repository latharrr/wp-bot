from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core API
    api_key: str = "change-me-api-key"
    jwt_secret: str = "change-me-jwt-secret"
    jwt_expiry_hours: int = 24

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
    whatsapp_use_pairing_code: bool = True
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
    def alert_recipient_list(self) -> list[str]:
        return [addr.strip() for addr in self.whatsapp_alert_recipients.split(",") if addr.strip()]

    @property
    def baileys_project_path(self) -> Path:
        return Path(self.baileys_project_dir).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
