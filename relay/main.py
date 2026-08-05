import logging
import sys
import time

from relay.config import Config, ConfigError, load_dotenv
from relay.ninjaone_client import NinjaOneClient
from relay.telegram_client import TelegramClient
from relay.state import SeenAlertsStore, make_key
from relay.formatting import format_alert_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("relay")


def _passes_severity_filter(alert: dict, min_severities: list[str]) -> bool:
    if not min_severities:
        return True
    return (alert.get("severity") or "").upper() in min_severities


def _filter_by_organization(
    alerts: list[dict], organization_ids: list[int], device_organizations: dict[int, int | None]
) -> tuple[list[dict], list[dict], list[dict]]:
    """Divide gli alert in ammessi, di altre organizzazioni e non risolvibili.

    L'organizzazione di un alert non sta nel payload dell'alert: si ricava dal `deviceId`
    attraverso l'indice dei device. Un alert il cui device non compare nell'indice non viene
    ammesso, perche' ammetterlo significherebbe inoltrare in chat l'alert di un cliente
    diverso; il chiamante lo segnala pero' come anomalia, cosi' lo scarto non resta silenzioso."""
    kept: list[dict] = []
    foreign: list[dict] = []
    unresolved: list[dict] = []
    for alert in alerts:
        device_id = alert.get("deviceId")
        if device_id not in device_organizations:
            unresolved.append(alert)
        elif device_organizations[device_id] in organization_ids:
            kept.append(alert)
        else:
            foreign.append(alert)
    return kept, foreign, unresolved


def _select_alerts(
    ninjaone: NinjaOneClient, organization_ids: list[int]
) -> list[dict]:
    alerts = ninjaone.get_active_alerts(organization_ids)
    if not organization_ids:
        return alerts

    device_organizations = ninjaone.get_device_organizations()
    if any(alert.get("deviceId") not in device_organizations for alert in alerts):
        # Device aggiunto a NinjaOne dopo l'ultimo aggiornamento dell'indice: si rilegge
        # l'anagrafica una volta prima di concludere che l'alert non e' risolvibile.
        device_organizations = ninjaone.get_device_organizations(force_refresh=True)

    kept, foreign, unresolved = _filter_by_organization(
        alerts, organization_ids, device_organizations
    )
    if foreign:
        logger.info("%s alert scartati perche' di altre organizzazioni", len(foreign))
    if unresolved:
        logger.warning(
            "%s alert scartati: deviceId non presente nell'indice dei device (%s)",
            len(unresolved), sorted({alert.get("deviceId") for alert in unresolved}),
        )
    return kept


def run_once(
    ninjaone: NinjaOneClient,
    telegram: TelegramClient,
    state: SeenAlertsStore,
    mention_user_ids: list[int],
    min_severities: list[str],
    organization_ids: list[int],
    notify: bool = True,
) -> None:
    alerts = _select_alerts(ninjaone, organization_ids)
    current_uids = {alert["uid"] for alert in alerts}

    candidates = [alert for alert in alerts if state.is_new(make_key(alert["uid"], alert.get("severity")))]
    if candidates:
        severities_seen = sorted({(a.get("severity") or "n/d") for a in candidates})
        logger.info(
            "%s alert non ancora notificati su %s attivi (severity osservate: %s)",
            len(candidates), len(alerts), severities_seen,
        )

    primed = 0
    for alert in candidates:
        if not _passes_severity_filter(alert, min_severities):
            continue
        if notify:
            telegram.send_message(format_alert_message(alert, mention_user_ids))
        else:
            primed += 1
        state.mark_seen(make_key(alert["uid"], alert.get("severity")))

    if primed:
        logger.info("%s alert arretrati segnati come gia' visti senza notificarli", primed)

    state.prune_to(current_uids)


def main() -> None:
    load_dotenv()
    try:
        config = Config.from_env()
    except ConfigError as exc:
        logger.error("Configurazione non valida: %s", exc)
        raise SystemExit(1)

    ninjaone = NinjaOneClient(
        base_url=config.ninjaone_base_url,
        client_id=config.ninjaone_client_id,
        client_secret=config.ninjaone_client_secret,
        scope=config.ninjaone_scope,
    )
    telegram = TelegramClient(
        bot_token=config.telegram_bot_token,
        chat_id=config.telegram_chat_id,
        message_thread_id=config.telegram_message_thread_id,
    )
    state = SeenAlertsStore(config.state_file_path)

    if not config.organization_ids:
        logger.warning(
            "NINJAONE_ORGANIZATION_IDS non impostato: verranno inoltrati gli alert di "
            "TUTTE le organizzazioni visibili da questa app API, non solo quella prevista"
        )

    if "--prime" in sys.argv[1:]:
        # Avvio a freddo dopo un periodo di silenzio: gli alert gia' attivi verrebbero
        # notificati tutti insieme. Con --prime si esegue un solo giro che li registra come
        # gia' visti senza inviare nulla, cosi' in chat arrivano solo gli alert successivi.
        logger.info("Modalita' --prime: un solo giro, nessun messaggio inviato")
        run_once(
            ninjaone, telegram, state,
            config.telegram_mention_user_ids, config.min_severities, config.organization_ids,
            notify=False,
        )
        return

    logger.info(
        "Relay avviato: istanza NinjaOne=%s, polling ogni %ss, filtro severity=%s, filtro organizzazioni=%s",
        config.ninjaone_instance, config.poll_interval_seconds,
        config.min_severities or "nessuno (tutte le severity)",
        config.organization_ids or "nessuno (tutte le organizzazioni)",
    )
    while True:
        try:
            run_once(
                ninjaone, telegram, state,
                config.telegram_mention_user_ids, config.min_severities, config.organization_ids,
            )
        except Exception:
            logger.exception("Errore durante il ciclo di polling, riprovo al prossimo giro")
        time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    main()
