import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from supabase import Client, create_client

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Contact:
    id: str
    nome: str
    telefone: str


class SupabaseContactRepository:
    def __init__(
        self,
        url: str,
        key: str,
        table_name: str,
        status_column: str = "status_envio",
    ) -> None:
        self._client: Client = create_client(url, key)
        self._table_name = table_name
        self._status_column = status_column

    def fetch_contacts(self, limit: int) -> list[Contact]:
        """Busca apenas contatos com status 'pendente' (idempotência)."""
        logger.info(
            "Buscando até %s contato(s) pendente(s) na tabela '%s'",
            limit,
            self._table_name,
        )

        response = (
            self._client.table(self._table_name)
            .select("id, nome, telefone")
            .eq(self._status_column, "pendente")
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

    def mark_sent(
        self,
        contact_id: str,
        status: Literal["enviado", "erro"],
        error_msg: str | None = None,
    ) -> None:
        """
        Atualiza o status do contato após tentativa de envio.

        status esperado: 'enviado' | 'erro'
        Garante que o script seja idempotente: contatos marcados como 'enviado'
        nao serao retornados em execucoes futuras.
        """
        # Apenas o status é sempre atualizado.
        # enviado_em só faz sentido semântico quando a mensagem foi enviada com sucesso.
        # erro_msg só é incluído quando há descrição do erro.
        payload: dict = {self._status_column: status}

        if status == "enviado":
            payload["enviado_em"] = datetime.now(tz=timezone.utc).isoformat()

        if error_msg:
            payload["erro_msg"] = error_msg[:500]  # limita para nao estourar o campo


        try:
            self._client.table(self._table_name).update(payload).eq("id", contact_id).execute()
            logger.debug("Status atualizado para '%s' (id=%s)", status, contact_id)
        except Exception:
            # Nao propaga: falha no UPDATE nao deve mascarar o resultado do envio
            logger.exception(
                "Falha ao atualizar status do contato id=%s para '%s'",
                contact_id,
                status,
            )

