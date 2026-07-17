import json
import os

_KEY_SEP = "|"


def make_key(uid: str, severity: str | None) -> str:
    """Chiave di deduplica: uid + severity, non il solo uid. Cosi' un alert che peggiora
    (stesso uid, severity che sale da MINOR a CRITICAL) viene rivalutato dal filtro invece
    di restare per sempre "gia' visto" alla prima severity osservata."""
    return f"{uid}{_KEY_SEP}{severity or ''}"


class SeenAlertsStore:
    """Persiste su file le chiavi (uid+severity) degli alert gia' notificati, per non
    duplicare i messaggi tra un polling e il successivo. Formato: JSON list di stringhe."""

    def __init__(self, path: str):
        self._path = path
        self._seen: set[str] = self._load()

    def _load(self) -> set[str]:
        if not os.path.exists(self._path):
            return set()
        with open(self._path, "r", encoding="utf-8") as f:
            return set(json.load(f))

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._path) or ".", exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(sorted(self._seen), f, indent=2)

    def is_new(self, key: str) -> bool:
        return key not in self._seen

    def mark_seen(self, key: str) -> None:
        self._seen.add(key)
        self._save()

    def prune_to(self, current_uids: set[str]) -> None:
        """Rimuove dallo stato le chiavi di alert non piu' attivi (risolti), cosi' il file
        non cresce indefinitamente e un uid futuro riemesso da NinjaOne viene rivalutato da
        capo invece di restare segnato come gia' visto per sempre."""
        remaining = {key for key in self._seen if key.split(_KEY_SEP, 1)[0] in current_uids}
        if remaining != self._seen:
            self._seen = remaining
            self._save()
