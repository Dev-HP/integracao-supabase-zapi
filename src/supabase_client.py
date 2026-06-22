import logging
from dataclasses import dataclass

from supabase import Client, create_client

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Contact:
    id: str
    nome: str
    telefone: str


class SupabaseContactRepository:
    def __init__(self, url: str, key: str, table_name: str) -> None:
        self._client: Client = create_client(url, key)
        self._table_name = table_name

    def fetch_contacts(self, limit: int) -> list[Contact]:
        logger.info("Buscando até %s contato(s) na tabela '%s'", limit, self._table_name)

        response = (
            self._client.table(self._table_name)
            .select("id, nome, telefone")
            .limit(limit)
            .execute()
        )

        contacts: list[Contact] = []
        for row in response.data or []:
            nome = (row.get("nome") or "").strip()
            telefone = (row.get("telefone") or "").strip()
            contact_id = str(row.get("id", ""))

            if not nome or not telefone:
                logger.warning(
                    "Contato ignorado (id=%s): nome ou telefone ausente",
                    contact_id or "desconhecido",
                )
                continue

            contacts.append(Contact(id=contact_id, nome=nome, telefone=telefone))

        logger.info("%s contato(s) válido(s) encontrado(s)", len(contacts))
        return contacts
