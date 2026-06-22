import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_key: str
    zapi_instance_id: str
    zapi_token: str
    zapi_client_token: str | None
    max_contacts: int
    table_name: str
    status_column: str
    log_level: str

    @property
    def zapi_send_url(self) -> str:
        return (
            f"https://api.z-api.io/instances/{self.zapi_instance_id}"
            f"/token/{self.zapi_token}/send-text"
        )


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Variável de ambiente obrigatória ausente: {name}")
    return value


def _require_int(name: str, default: int, minimum: int = 1) -> int:
    """Lê uma variável de ambiente como inteiro com validação e valor mínimo."""
    raw = os.getenv(name, str(default)).strip()
    try:
        return max(minimum, int(raw))
    except ValueError:
        raise ValueError(
            f"Variável '{name}' deve ser um inteiro, mas recebeu: '{raw}'"
        )


def load_settings() -> Settings:
    return Settings(
        supabase_url=_require("SUPABASE_URL"),
        supabase_key=_require("SUPABASE_KEY"),
        zapi_instance_id=_require("ZAPI_INSTANCE_ID"),
        zapi_token=_require("ZAPI_TOKEN"),
        zapi_client_token=os.getenv("ZAPI_CLIENT_TOKEN", "").strip() or None,
        max_contacts=_require_int("MAX_CONTACTS", default=3, minimum=1),
        table_name=os.getenv("TABLE_NAME", "contatos").strip() or "contatos",
        status_column=os.getenv("STATUS_COLUMN", "status_envio").strip() or "status_envio",
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
