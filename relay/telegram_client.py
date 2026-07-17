import time
import logging

import requests

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"
MAX_RETRIES = 3


class TelegramSendError(Exception):
    pass


class TelegramClient:
    def __init__(self, bot_token: str, chat_id: str, message_thread_id: int | None = None):
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._message_thread_id = message_thread_id

    def send_message(self, html_text: str) -> None:
        payload = {
            "chat_id": self._chat_id,
            "text": html_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if self._message_thread_id is not None:
            payload["message_thread_id"] = self._message_thread_id

        url = f"{TELEGRAM_API_BASE}/bot{self._bot_token}/sendMessage"
        for attempt in range(1, MAX_RETRIES + 1):
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                return
            if response.status_code == 429:
                retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                logger.warning(
                    "Rate limit Telegram, attendo %s secondi (tentativo %s/%s)",
                    retry_after, attempt, MAX_RETRIES,
                )
                time.sleep(retry_after)
                continue
            raise TelegramSendError(f"Invio Telegram fallito ({response.status_code}): {response.text[:300]}")
        raise TelegramSendError("Invio Telegram fallito dopo i tentativi per rate limiting ripetuto")
