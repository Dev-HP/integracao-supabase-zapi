from dataclasses import dataclass
from typing import Protocol


@dataclass
class MessageResult:
    success: bool
    message_id: str | None = None
    error: str | None = None


class MessagingService(Protocol):
    # interface base — qualquer provedor (Z-API, Twilio...) implementa isso

    def send_text_message(self, phone: str, message: str) -> MessageResult:
        ...
