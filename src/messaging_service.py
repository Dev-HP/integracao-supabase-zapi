from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MessageResult:
    success: bool
    message_id: str | None = None
    error: str | None = None


class MessagingService(ABC):
    # interface base — qualquer provedor (Z-API, Twilio...) implementa isso

    @abstractmethod
    def send_text_message(self, phone: str, message: str) -> MessageResult:
        pass
