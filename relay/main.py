import logging
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


def _belongs_to_organizations(alert: dict, organization_ids: list[int]) -> bool:
    if not organization_ids:
        return True
    device = alert.get("device") or {}
    return device.get("organizationId") in organization_ids


def run_once(
    ninjaone: NinjaOneClient,
    telegram: TelegramClient,
    state: SeenAlertsStore,
    mention_user_ids: list[int],
    min_severities: list[str],
    organization_ids: list[int],
) -> None:
    alerts = [
        alert for alert in ninjaone.get_active_alerts()
        if _belongs_to_organizations(alert, organization_ids)
    ]
    current_uids = {alert["uid"] for alert in alerts}

    candidates = [alert for alert in alerts if state.is_new(make_key(alert["uid"], alert.get("severity")))]
    if candidates:
        severities_seen = sorted({(a.get("severity") or "n/d") for a in candidates})
        logger.info(
            "%s alert non ancora notificati su %s attivi (severity osservate: %s)",
            len(candidates), len(alerts), severities_seen,
        )

    for alert in candidates:
        if not _passes_severity_filter(alert, min_severities):
            continue
        text = format_alert_message(alert, mention_user_ids)
        telegram.send_message(text)
        state.mark_seen(make_key(alert["uid"], alert.get("severity")))

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
