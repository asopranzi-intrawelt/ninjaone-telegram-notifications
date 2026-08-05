import time
import logging

import requests

logger = logging.getLogger(__name__)

TOKEN_PATH = "/ws/oauth/token"
ALERTS_PATH = "/v2/alerts"
DEVICES_PATH = "/v2/devices"

# Margine di sicurezza prima della scadenza reale del token, per rinnovarlo in anticipo.
TOKEN_EXPIRY_MARGIN_SECONDS = 60

# Durata della cache dell'indice deviceId -> organizationId. L'anagrafica dei device cambia
# di rado, quindi si rilegge ogni quarto d'ora invece che a ogni giro di polling; un device
# nuovo che compare prima della scadenza forza comunque un aggiornamento immediato.
DEVICE_INDEX_TTL_SECONDS = 900


class NinjaOneAuthError(Exception):
    pass


def device_filter_expression(organization_ids: list[int]) -> str | None:
    """Traduce una lista di organizzazioni nel device filter di NinjaOne, il parametro di
    query `df`. La sintassi e' verificata sull'istanza reale: `org=<id>` per una singola
    organizzazione e `org in (<id>,<id>)` per piu' di una, mentre la forma `org=<id>,<id>`
    viene rifiutata dal server con InvalidFilterException."""
    if not organization_ids:
        return None
    if len(organization_ids) == 1:
        return f"org={organization_ids[0]}"
    return "org in (" + ",".join(str(oid) for oid in organization_ids) + ")"


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
        self._device_index: dict[int, int | None] | None = None
        self._device_index_expires_at: float = 0.0

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

    def _get(self, path: str, params: dict | None = None):
        token = self._ensure_token()
        response = requests.get(
            self._base_url + path,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30,
        )
        if response.status_code == 401:
            # Token scaduto lato server nonostante il margine locale: forza un rinnovo e riprova una volta.
            self._access_token = None
            token = self._ensure_token()
            response = requests.get(
                self._base_url + path,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                timeout=30,
            )
        response.raise_for_status()
        return response.json()

    def get_active_alerts(self, organization_ids: list[int] | None = None) -> list[dict]:
        """Ritorna la lista degli alert attivi (condizioni attualmente in trigger).

        Quando sono indicate delle organizzazioni il filtro viene chiesto anche al server con
        il parametro `df`, cosi' gli alert degli altri clienti non vengono nemmeno scaricati.
        Resta comunque autoritativo il controllo lato client svolto in `run_once`, perche' un
        `df` non applicato dal server passerebbe altrimenti inosservato lasciando uscire gli
        alert delle altre organizzazioni."""
        expression = device_filter_expression(organization_ids or [])
        return self._get(ALERTS_PATH, {"df": expression} if expression else None)

    def get_device_organizations(self, force_refresh: bool = False) -> dict[int, int | None]:
        """Ritorna la mappa deviceId -> organizationId, con cache a scadenza.

        Serve perche' l'oggetto Alert restituito da /v2/alerts porta solo `deviceId`: il
        campo `organizationId` non e' presente nel payload (verificato sull'istanza reale) e
        va risolto attraverso l'anagrafica dei device."""
        now = time.monotonic()
        if force_refresh or self._device_index is None or now >= self._device_index_expires_at:
            devices = self._get(DEVICES_PATH)
            self._device_index = {
                device["id"]: device.get("organizationId") for device in devices
            }
            self._device_index_expires_at = now + DEVICE_INDEX_TTL_SECONDS
            logger.info("Indice device aggiornato: %s device noti", len(self._device_index))
        return self._device_index
