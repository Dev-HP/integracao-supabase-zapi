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


def load_settings() -> Settings:
    return Settings(
        supabase_url=_require("SUPABASE_URL"),
        supabase_key=_require("SUPABASE_KEY"),
        zapi_instance_id=_require("ZAPI_INSTANCE_ID"),
        zapi_token=_require("ZAPI_TOKEN"),
        zapi_client_token=os.getenv("ZAPI_CLIENT_TOKEN", "").strip() or None,
        max_contacts=max(1, int(os.getenv("MAX_CONTACTS", "3"))),
        table_name=os.getenv("TABLE_NAME", "contatos").strip() or "contatos",
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
