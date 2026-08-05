---
generated-from-commit: 91c9917
generated-from-branch: main
generated-date: 2026-07-16
covers-paths:
  - relay/**
  - tests/**
  - requirements.txt
last-verified-commit: ac34b7b
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
relay/config.py            Config, letta da variabili d'ambiente (.env) con un loader nativo
                            (load_dotenv, nessuna dipendenza esterna: BOM tollerato, ultima
                            occorrenza valorizzata vincente, ambiente reale non sovrascritto),
                            validazione dei campi obbligatori, mappa delle istanze NinjaOne
                            (eu/us/ca/us2/fed/oc) e accettazione di un URL https completo per
                            le istanze brandizzate white-label
relay/ninjaone_client.py   NinjaOneClient: OAuth2 client-credentials verso /ws/oauth/token,
                            rinnovo automatico del token, _get() con un solo retry su 401,
                            get_active_alerts() su GET /v2/alerts con device filter df,
                            get_device_organizations() su GET /v2/devices che costruisce la
                            mappa deviceId -> organizationId con cache a 900 secondi;
                            device_filter_expression() traduce la lista di organizzazioni
                            nella sintassi df (org=<id>, oppure org in (<id>,<id>))
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
relay/main.py               run_once() esegue un ciclo di polling: _select_alerts() legge gli
                            alert e ne risolve l'organizzazione, _passes_severity_filter()
                            applica il filtro di severity, e le severity osservate finiscono
                            nei log per calibrazione. _filter_by_organization() partiziona gli
                            alert in ammessi, di altre organizzazioni e non risolvibili.
                            main() e' l'entrypoint, con il loop infinito, la gestione errori
                            per-ciclo e il flag --prime che assorbe l'arretrato segnandolo
                            come visto senza inviare messaggi
tests/test_relay.py        23 test con requests mockato: notifica, escaping HTML, dati
                            mancanti, deduplica, pruning, filtro di severity ed escalation,
                            filtro per organizzazione (df inviato al server, device di altra
                            organizzazione, device non risolvibile, refresh dell'indice),
                            priming, sintassi del device filter, Config e loader .env
```

Esecuzione: `python -m relay.main` dalla radice del progetto, con un file `.env` (da
`.env.example`) o le variabili già esportate nell'ambiente. Un solo giro senza invii, per
assorbire gli alert già attivi dopo un fermo prolungato, si ottiene con
`python -m relay.main --prime`.

L'organizzazione di un alert non e' deducibile dal solo alert: il payload di `GET /v2/alerts`
porta `deviceId` e non un oggetto `device` annidato, quindi `organizationId` si risolve
attraverso l'anagrafica dei device. Il filtro viene chiesto due volte, al server con il
parametro `df` e di nuovo lato client sulla mappa dei device, e in caso di dubbio scarta:
il dettaglio del perche' sta in ADR-004.

## Riferimenti a snippet

`relay/ninjaone_client.py:NinjaOneClient._fetch_token` — richiesta OAuth2 client credentials.
`relay/ninjaone_client.py:NinjaOneClient.get_active_alerts` — lettura alert attivi, con device filter.
`relay/ninjaone_client.py:NinjaOneClient.get_device_organizations` — mappa deviceId -> organizationId.
`relay/ninjaone_client.py:device_filter_expression` — sintassi del parametro df.
`relay/main.py:_select_alerts` — lettura alert e risoluzione dell'organizzazione.
`relay/main.py:_filter_by_organization` — partizione in ammessi, altrui, non risolvibili.
`relay/main.py:run_once` — logica di deduplica e invio.
`relay/formatting.py:format_alert_message` — mappatura campi Alert -> testo Telegram.
