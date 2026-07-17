import time
import logging

import requests

logger = logging.getLogger(__name__)

TOKEN_PATH = "/ws/oauth/token"
ALERTS_PATH = "/v2/alerts"

# Margine di sicurezza prima della scadenza reale del token, per rinnovarlo in anticipo.
TOKEN_EXPIRY_MARGIN_SECONDS = 60


class NinjaOneAuthError(Exception):
    pass


class NinjaOneClient:
    """Client minimale per NinjaOne Public API v2, flusso OAuth2 client credentials.

    Endpoint e schema verificati contro lo spec OpenAPI ufficiale
    (ninjaOne-API-core-resources.yaml) e il modulo PowerShell homotechsual/NinjaOne.
    """

    def __init__(self, base_url: str, client_id: str, client_secret: str, scope: str):
        self._base_url = base_url.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    def _fetch_token(self) -> None:
        response = requests.post(
            self._base_url + TOKEN_PATH,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": self._scope,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        if response.status_code != 200:
            raise NinjaOneAuthError(
                f"Token OAuth2 rifiutato ({response.status_code}): {response.text[:300]}"
            )
        payload = response.json()
        self._access_token = payload["access_token"]
        self._token_expires_at = time.monotonic() + payload["expires_in"] - TOKEN_EXPIRY_MARGIN_SECONDS
        logger.info("Nuovo token NinjaOne ottenuto, valido per %s secondi", payload["expires_in"])

    def _ensure_token(self) -> str:
        if self._access_token is None or time.monotonic() >= self._token_expires_at:
            self._fetch_token()
        return self._access_token

    def get_active_alerts(self) -> list[dict]:
        """Ritorna la lista degli alert attivi (condizioni attualmente in trigger)."""
        token = self._ensure_token()
        response = requests.get(
            self._base_url + ALERTS_PATH,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if response.status_code == 401:
            # Token scaduto lato server nonostante il margine locale: forza un rinnovo e riprova una volta.
            self._access_token = None
            token = self._ensure_token()
            response = requests.get(
                self._base_url + ALERTS_PATH,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
        response.raise_for_status()
        return response.json()
