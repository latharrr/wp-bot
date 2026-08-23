"""Spawns and controls the Node/TypeScript Baileys bridge subprocess.

Mirrors the process-management pattern from the reference repo's BaileysBridgeProcessManager:
FastAPI's lifespan starts the bridge, injects config via env vars, and a pairing-code (or QR)
request resets any existing session before starting a fresh run.
"""
import asyncio
import logging
import os
import shutil
import signal
import subprocess
from pathlib import Path
from typing import Optional

from app.core.config import Settings, get_settings
from app.services.whatsapp_session_state import ConnectionStatus, get_session_state

logger = logging.getLogger(__name__)

PAIRING_CODE_TIMEOUT_SECONDS = 45
PAIRING_CODE_POLL_INTERVAL_SECONDS = 0.5
QR_CODE_TIMEOUT_SECONDS = 20
QR_CODE_POLL_INTERVAL_SECONDS = 0.5


class BridgeProcessManager:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._process: Optional[subprocess.Popen] = None

    @property
    def project_dir(self) -> Path:
        return self._settings.baileys_project_path

    @property
    def auth_dir(self) -> Path:
        return Path(self._settings.baileys_auth_dir).resolve()

    @property
    def pairing_code_file(self) -> Path:
        return self.project_dir / ".pairing-code.json"

    @property
    def qr_code_file(self) -> Path:
        return self.project_dir / ".qr-code.json"

    def _build_env(self, pairing_phone_number: Optional[str] = None) -> dict:
        env = os.environ.copy()
        env.update(
            {
                "WHATSAPP_INTERNAL_BASE_URL": self._settings.whatsapp_internal_base_url,
                "WHATSAPP_INTERNAL_TOKEN": self._settings.whatsapp_internal_token,
                "WHATSAPP_BRIDGE_CONTROL_TOKEN": self._settings.whatsapp_bridge_control_token,
                "BAILEYS_AUTH_DIR": str(self.auth_dir),
                "BAILEYS_LOG_LEVEL": self._settings.baileys_log_level,
                "BAILEYS_LOG_DIR": str(self._settings.baileys_log_path),
                "PAIRING_CODE_FILE": str(self.pairing_code_file),
                "QR_CODE_FILE": str(self.qr_code_file),
            }
        )
        if pairing_phone_number:
            env["WHATSAPP_USE_PAIRING_CODE"] = "true"
            env["WHATSAPP_PHONE_NUMBER"] = pairing_phone_number
        return env

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self, pairing_phone_number: Optional[str] = None) -> None:
        if self.is_running():
            logger.info("Bridge already running, skipping start")
            return

        if not shutil.which("npx"):
            raise RuntimeError("npx not found on PATH; install Node 20+ to run the WhatsApp bridge")

        env = self._build_env(pairing_phone_number)
        logger.info("Starting WhatsApp bridge subprocess (cwd=%s)", self.project_dir)
        self._process = subprocess.Popen(
            ["npx", "tsx", "bridge.ts"],
            cwd=str(self.project_dir),
            env=env,
        )
        get_session_state().status = ConnectionStatus.CONNECTING

    def stop(self) -> None:
        if not self.is_running():
            self._process = None
            return
        logger.info("Stopping WhatsApp bridge subprocess")
        assert self._process is not None
        self._process.send_signal(signal.SIGTERM)
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
        self._process = None
        get_session_state().status = ConnectionStatus.DISCONNECTED

    def reset_session(self) -> None:
        """Stop the bridge and delete stored Baileys auth so the next start requires a fresh pairing."""
        self.stop()
        if self.auth_dir.exists():
            shutil.rmtree(self.auth_dir)
        if self.pairing_code_file.exists():
            self.pairing_code_file.unlink()
        if self.qr_code_file.exists():
            self.qr_code_file.unlink()

    async def request_pairing_code(self, phone_number: str) -> str:
        """Reset any existing session, start the bridge in pairing mode, wait for the pairing code."""
        self.reset_session()
        self.start(pairing_phone_number=phone_number)
        get_session_state().status = ConnectionStatus.PAIRING
        get_session_state().pairing_code = None

        elapsed = 0.0
        while elapsed < PAIRING_CODE_TIMEOUT_SECONDS:
            if self.pairing_code_file.exists():
                try:
                    import json

                    data = json.loads(self.pairing_code_file.read_text())
                    code = data.get("code")
                    if code:
                        get_session_state().pairing_code = code
                        return code
                except (json.JSONDecodeError, OSError):
                    pass
            await asyncio.sleep(PAIRING_CODE_POLL_INTERVAL_SECONDS)
            elapsed += PAIRING_CODE_POLL_INTERVAL_SECONDS

        raise TimeoutError("Timed out waiting for the bridge to generate a pairing code")

    async def start_qr_session(self) -> str:
        """Reset any existing session, start the bridge fresh in QR mode, wait for the first QR.

        QR-code linking is the reliable path here: pairing-code linking (request_pairing_code
        above) reliably gets a code back from WhatsApp but the session is then rejected within
        seconds (verified against a live connection -- a plain QR-mode connection with no
        pairing-code request stays open indefinitely with no such rejection). The QR itself
        rotates roughly every 20s while unscanned; callers should keep polling get_qr_code()
        for a newer generated_at rather than treating the first one as final.
        """
        self.reset_session()
        self.start()
        get_session_state().status = ConnectionStatus.PAIRING

        elapsed = 0.0
        while elapsed < QR_CODE_TIMEOUT_SECONDS:
            qr = self.get_qr_code()
            if qr:
                return qr["qr_data_url"]
            await asyncio.sleep(QR_CODE_POLL_INTERVAL_SECONDS)
            elapsed += QR_CODE_POLL_INTERVAL_SECONDS

        raise TimeoutError("Timed out waiting for the bridge to generate a QR code")

    def get_qr_code(self) -> Optional[dict]:
        if not self.qr_code_file.exists():
            return None
        try:
            import json

            return json.loads(self.qr_code_file.read_text())
        except (json.JSONDecodeError, OSError):
            return None


_manager: Optional[BridgeProcessManager] = None


def get_bridge_manager() -> BridgeProcessManager:
    global _manager
    if _manager is None:
        _manager = BridgeProcessManager()
    return _manager
