import os
from dataclasses import dataclass, field

NINJAONE_INSTANCE_HOSTS = {
    "eu": "https://eu.ninjarmm.com",
    "oc": "https://oc.ninjarmm.com",
    "us": "https://app.ninjarmm.com",
    "ca": "https://ca.ninjarmm.com",
    "us2": "https://us2.ninjarmm.com",
    "fed": "https://fed.ninjarmm.com",
}


class ConfigError(Exception):
    pass


def load_dotenv(path: str = ".env") -> None:
    """Carica le variabili da un file .env senza sovrascrivere l'ambiente reale.

    Formato supportato: righe KEY=VALUE, commenti con # e righe vuote ignorati,
    doppi apici o apici singoli opzionali attorno al valore. Le righe con valore
    vuoto (KEY=) non registrano nulla e, se una chiave compare piu volte, vince
    l'ultima occorrenza valorizzata: cosi un template con la riga vuota in testa
    non maschera il valore reale aggiunto piu in basso.
    """
    if not os.path.exists(path):
        return
    parsed: dict[str, str] = {}
    # utf-8-sig assorbe l'eventuale BOM che gli editor Windows premettono al file.
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if key and value:
                parsed[key] = value
    for key, value in parsed.items():
        os.environ.setdefault(key, value)


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"Variabile d'ambiente mancante: {name}")
    return value


@dataclass
class Config:
    ninjaone_instance: str
    ninjaone_base_url: str
    ninjaone_client_id: str
    ninjaone_client_secret: str
    ninjaone_scope: str
    telegram_bot_token: str
    telegram_chat_id: str
    telegram_message_thread_id: int | None
    telegram_mention_user_ids: list[int] = field(default_factory=list)
    poll_interval_seconds: int = 120
    state_file_path: str = "./data/seen_alerts.json"
    min_severities: list[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "Config":
        instance = _require("NINJAONE_INSTANCE").lower()
        if instance.startswith("https://"):
            # Dominio brandizzato (es. istanza white-label di un MSP): si usa come base URL.
            base_url = instance.rstrip("/")
        elif instance in NINJAONE_INSTANCE_HOSTS:
            base_url = NINJAONE_INSTANCE_HOSTS[instance]
        else:
            raise ConfigError(
                f"NINJAONE_INSTANCE={instance!r} non valido, atteso uno tra "
                f"{sorted(NINJAONE_INSTANCE_HOSTS)} oppure un URL https:// completo"
            )

        thread_id_raw = os.environ.get("TELEGRAM_MESSAGE_THREAD_ID", "").strip()
        mention_ids_raw = os.environ.get("TELEGRAM_MENTION_USER_IDS", "").strip()
        min_severities_raw = os.environ.get("NINJAONE_MIN_SEVERITIES", "").strip()

        return cls(
            ninjaone_instance=instance,
            ninjaone_base_url=base_url,
            ninjaone_client_id=_require("NINJAONE_CLIENT_ID"),
            ninjaone_client_secret=_require("NINJAONE_CLIENT_SECRET"),
            ninjaone_scope=os.environ.get("NINJAONE_SCOPE", "monitoring"),
            telegram_bot_token=_require("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=_require("TELEGRAM_CHAT_ID"),
            telegram_message_thread_id=int(thread_id_raw) if thread_id_raw else None,
            telegram_mention_user_ids=[
                int(uid) for uid in mention_ids_raw.split(",") if uid.strip()
            ],
            poll_interval_seconds=int(os.environ.get("POLL_INTERVAL_SECONDS", "120")),
            state_file_path=os.environ.get("STATE_FILE_PATH", "./data/seen_alerts.json"),
            min_severities=[
                s.strip().upper() for s in min_severities_raw.split(",") if s.strip()
            ],
        )
