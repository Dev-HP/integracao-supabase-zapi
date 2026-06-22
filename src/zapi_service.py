import logging
import re
import time

import requests

from src.messaging_service import MessagingService, MessageResult

logger = logging.getLogger(__name__)

PHONE_DIGITS = re.compile(r"\D+")


def normalize_phone(phone: str) -> str:
    return PHONE_DIGITS.sub("", phone)


class ZApiMessagingService(MessagingService):

    def __init__(
        self,
        send_url: str,
        client_token: str | None = None,
        max_retries: int = 3,
        timeout: int = 30,
    ) -> None:
        self._send_url = send_url
        self._client_token = client_token
        self._max_retries = max_retries
        self._timeout = timeout

    def send_text_message(self, phone: str, message: str) -> MessageResult:
        normalized_phone = normalize_phone(phone)

        if not normalized_phone:
            return MessageResult(success=False, error="Telefone inválido")

        headers = {"Content-Type": "application/json"}
        if self._client_token:
            headers["Client-Token"] = self._client_token

        payload = {"phone": normalized_phone, "message": message}
        last_error: str | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info(
                    "Enviando para %s (tentativa %s/%s)",
                    normalized_phone, attempt, self._max_retries,
                )

                response = requests.post(
                    self._send_url,
                    json=payload,
                    headers=headers,
                    timeout=self._timeout,
                )

                # 5xx = problema do servidor, vale tentar de novo
                if response.status_code >= 500:
                    last_error = f"Erro {response.status_code}: {response.text}"
                    logger.warning("Servidor Z-API retornou erro: %s", last_error)
                    if attempt < self._max_retries:
                        time.sleep(2 ** (attempt - 1))
                        continue
                    return MessageResult(success=False, error=last_error)

                response.raise_for_status()
                data = response.json()
                message_id = data.get("messageId") or data.get("zaapId") or data.get("id")
                logger.debug("Resposta Z-API: %s", data)
                logger.info("Enviado para %s (id=%s)", normalized_phone, message_id)

                return MessageResult(success=True, message_id=message_id)

            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else None
                # 4xx não adianta tentar de novo
                if status is not None and 400 <= status < 500:
                    error_msg = f"Erro {status}: {exc.response.text if exc.response else str(exc)}"
                    logger.error("Erro permanente para %s: %s", normalized_phone, error_msg)
                    return MessageResult(success=False, error=error_msg)
                last_error = str(exc)
                logger.warning("Erro HTTP para %s: %s", normalized_phone, last_error)

            except requests.RequestException as exc:
                last_error = str(exc)
                logger.warning("Erro de rede para %s: %s", normalized_phone, last_error)

            if attempt < self._max_retries:
                time.sleep(2 ** (attempt - 1))

        return MessageResult(
            success=False,
            error=f"Falha após {self._max_retries} tentativas: {last_error}"
        )

