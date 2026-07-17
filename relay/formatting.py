import html

# Mappa emoji per severity, calibrata sui valori NinjaOne piu' comuni (CRITICAL/MAJOR/MODERATE/MINOR).
# I valori esatti restituiti dall'istanza reale non sono ancora verificati (nessuna credenziale
# NinjaOne configurata finora): il fallback "sconosciuta" rende visibile in chat un valore non
# mappato, cosi' la mappa si calibra guardando i primi alert reali invece di indovinare.
SEVERITY_EMOJI = {
    "CRITICAL": "🔴",
    "MAJOR": "🔴",
    "MODERATE": "🟠",
    "MINOR": "🟡",
    "NONE": "⚪",
}
UNKNOWN_SEVERITY_EMOJI = "⚪"


def _mention_html(user_ids: list[int]) -> str:
    return " ".join(f'<a href="tg://user?id={uid}">utente</a>' for uid in user_ids)


def format_alert_message(alert: dict, mention_user_ids: list[int]) -> str:
    """Costruisce il testo HTML del messaggio Telegram a partire da un oggetto Alert
    dello schema NinjaOne (v2/alerts). Campi verificati sullo spec OpenAPI ufficiale.
    Formato compatto: titolo con emoji di severity, device, messaggio, menzioni. Niente
    priorita' ne' timestamp esplicito (Telegram mostra gia' l'orario di ogni messaggio)."""
    device = alert.get("device") or {}
    device_name = html.escape(device.get("displayName") or f"device #{alert.get('deviceId')}")
    message = html.escape(alert.get("message") or "(nessun messaggio)")
    severity_raw = (alert.get("severity") or "").upper()
    emoji = SEVERITY_EMOJI.get(severity_raw, UNKNOWN_SEVERITY_EMOJI)
    condition = html.escape(alert.get("conditionName") or alert.get("sourceType") or "n/d")

    lines = [
        f"{emoji} <b>{condition}</b> — {device_name}",
        message,
    ]
    if mention_user_ids:
        lines.append(_mention_html(mention_user_ids))
    return "\n".join(lines)
