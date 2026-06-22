#!/usr/bin/env python3
# Desafio b2bflow — lê contatos do Supabase e manda mensagem via Z-API
import logging
import sys

from src.config import load_settings
from src.logger import setup_logging
from src.supabase_client import SupabaseContactRepository
from src.zapi_service import ZApiMessagingService


def build_message(nome: str) -> str:
    return f"Olá, {nome} tudo bem com você?"


def main() -> int:
    try:
        settings = load_settings()
    except ValueError as e:
        print(f"[ERRO] Erro de configuração: {e}")
        return 1

    setup_logging(settings.log_level)
    logger = logging.getLogger(__name__)

    logger.info("Iniciando — limite: %d contato(s)", settings.max_contacts)

    try:
        contact_repo = SupabaseContactRepository(
            url=settings.supabase_url,
            key=settings.supabase_key,
            table_name=settings.table_name,
        )
        contacts = contact_repo.fetch_contacts(limit=settings.max_contacts)
    except Exception:
        logger.exception("Falha ao buscar contatos")
        return 1

    if not contacts:
        logger.warning("Nenhum contato encontrado")
        return 0

    messaging = ZApiMessagingService(
        send_url=settings.zapi_send_url,
        client_token=settings.zapi_client_token,
        max_retries=3,
        timeout=30,
    )

    success_count = 0
    failure_count = 0

    for contact in contacts:
        logger.info("Processando: %s (%s)", contact.nome, contact.telefone)
        result = messaging.send_text_message(
            phone=contact.telefone,
            message=build_message(contact.nome),
        )

        if result.success:
            success_count += 1
            logger.info("[OK] %s", contact.nome)
        else:
            failure_count += 1
            logger.error("[FALHA] %s: %s", contact.nome, result.error)

    logger.info("Fim — %d enviados, %d falhas", success_count, failure_count)
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

