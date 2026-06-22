#!/usr/bin/env python3
# Desafio b2bflow — lê contatos do Supabase e manda mensagem via Z-API
import logging
import sys

# Template da mensagem como constante de módulo:
# evita a sobrecarga de uma chamada de função por contato e deixa
# o texto facilmente localizável para edição futura.
MESSAGE_TEMPLATE = "Olá, {nome} tudo bem com você?"

from src.config import load_settings
from src.logger import setup_logging
from src.supabase_client import SupabaseContactRepository
from src.zapi_service import ZApiMessagingService


def main() -> int:
    try:
        settings = load_settings()
    except ValueError as e:
        # sys.exit propaga o erro diretamente para o SO/orquestrador (cron, CI, Docker).
        # Um print solto seria ignorado por ferramentas de monitoramento que leem exit codes.
        sys.exit(f"[ERRO FATAL] Falha de configuração: {e}")

    setup_logging(settings.log_level)
    logger = logging.getLogger(__name__)

    logger.info("Iniciando — limite: %d contato(s)", settings.max_contacts)

    try:
        contact_repo = SupabaseContactRepository(
            url=settings.supabase_url,
            key=settings.supabase_key,
            table_name=settings.table_name,
            status_column=settings.status_column,
        )
        # Busca apenas contatos com status 'pendente' — garante idempotência:
        # rodar o script múltiplas vezes não reenvia mensagens já enviadas.
        contacts = contact_repo.fetch_contacts(limit=settings.max_contacts)
    except Exception:
        logger.exception("Falha ao buscar contatos")
        return 1

    if not contacts:
        logger.warning("Nenhum contato pendente encontrado")
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
            message=MESSAGE_TEMPLATE.format(nome=contact.nome),
        )

        if result.success:
            success_count += 1
            logger.info("[OK] %s", contact.nome)
            # Marca como 'enviado' para não reprocessar em execuções futuras
            contact_repo.mark_sent(contact.id, "enviado")
        else:
            failure_count += 1
            logger.error("[FALHA] %s: %s", contact.nome, result.error)
            # Marca como 'erro' — pode ser reprocessado manualmente se necessário
            contact_repo.mark_sent(contact.id, "erro", error_msg=result.error)

    logger.info("Fim — %d enviados, %d falhas", success_count, failure_count)
    return 0 if failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

