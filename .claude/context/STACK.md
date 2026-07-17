---
generated-from-commit: PENDING-FIRST-COMMIT
generated-from-branch: main
generated-date: 2026-07-16
covers-paths:
  - relay/**
  - tests/**
  - requirements.txt
last-verified-commit: PENDING-FIRST-COMMIT
---

# Stack applicativo

> Documento di recupero più importante: tracciato, perché un collega che clona deve vederlo.
> Popolare leggendo il codice attuale, non inventare. Affinare `covers-paths` man mano.

## Stack e runtime

Python 3.13 (verificato con l'interprete di sviluppo, nessun vincolo di versione minima fissato
oltre 3.10 per via delle annotazioni `str | None` / `set[str]`). Unica dipendenza esterna:
`requests` (vedi `requirements.txt`). Nessun framework web: il relay è un processo long-running a
polling, non un server HTTP. Test con `unittest` di libreria standard, nessuna dipendenza di test
aggiuntiva.

## Alternative deliberatamente escluse

Modello push (webhook NinjaOne + tunnel pubblico verso il PC/VM locale): scartato per evitare di
esporre un endpoint su internet per un progetto a due utenti; il modello pull a polling elimina
il bisogno di un tunnel (Cloudflare Tunnel/ngrok) o di un IP pubblico.
Piattaforme no-code (n8n, Albato): scartate per mantenere il progetto autonomo, senza un servizio
di orchestrazione aggiuntivo da gestire.
Script PowerShell condition-triggered lato NinjaOne: scartato perché distribuirebbe il token del
bot Telegram sugli endpoint monitorati e coprirebbe solo gli alert di tipo "condizione
scriptabile", non l'intero flusso di alert.
`python-telegram-bot` o altre librerie Telegram dedicate: scartate, l'API Telegram usata (solo
`sendMessage`) è una singola chiamata HTTP POST, `requests` è sufficiente.

## Flussi di codice e ruolo architetturale dei file

```
relay/config.py            Config, letta da variabili d'ambiente (.env), con validazione dei
                            campi obbligatori e mappa delle istanze NinjaOne (eu/us/ca/us2/fed/oc)
relay/ninjaone_client.py   NinjaOneClient: OAuth2 client-credentials verso /ws/oauth/token,
                            rinnovo automatico del token, get_active_alerts() su GET /v2/alerts
relay/telegram_client.py   TelegramClient: sendMessage su api.telegram.org, retry con backoff
                            su risposta 429 rispettando retry_after
relay/state.py             SeenAlertsStore: persiste su data/seen_alerts.json (ignorato da git)
                            le chiavi uid+severity (make_key) degli alert già notificati, per
                            deduplica tra un poll e l'altro; prune_to rimuove le chiavi di alert
                            non più attivi; la chiave composita fa si' che un alert che peggiora
                            restando sullo stesso uid venga rivalutato dal filtro di severity
relay/formatting.py        format_alert_message: converte un oggetto Alert NinjaOne in testo
                            HTML compatto per Telegram (titolo con emoji di severity, device,
                            messaggio, menzioni via tg://user?id=<id>), con escaping
relay/main.py               run_once() esegue un ciclo di polling, applica il filtro di
                            severity (_passes_severity_filter) e logga le severity osservate
                            per calibrazione; main() e' l'entrypoint con il loop infinito e la
                            gestione errori per-ciclo
tests/test_relay.py        Test end-to-end con requests mockato: nuovo alert notificato,
                            escaping HTML, dati mancanti, deduplica, pruning degli alert risolti
```

Esecuzione: `python -m relay.main` dalla radice del progetto, con un file `.env` (da
`.env.example`) o le variabili già esportate nell'ambiente.

## Riferimenti a snippet

`relay/ninjaone_client.py:NinjaOneClient._fetch_token` — richiesta OAuth2 client credentials.
`relay/ninjaone_client.py:NinjaOneClient.get_active_alerts` — lettura alert attivi.
`relay/main.py:run_once` — logica di deduplica e invio.
`relay/formatting.py:format_alert_message` — mappatura campi Alert -> testo Telegram.
