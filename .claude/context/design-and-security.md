---
generated-from-commit: PENDING-FIRST-COMMIT
generated-from-branch: main
generated-date: 2026-07-16
covers-paths:
  - relay/**
last-verified-commit: PENDING-FIRST-COMMIT
---

# Design e sicurezza applicativa

> Popolare leggendo il codice attuale. I diagrammi referenziati vivono in `diagrams/` in
> corrispondenza uno a uno con i componenti descritti (sezione 7).

## Paradigmi di software design

Un modulo per responsabilità (config, client NinjaOne, client Telegram, stato locale,
formattazione, orchestrazione), nessuna classe base astratta o plugin system: lo scambio tra i
moduli avviene passando oggetti semplici (dict per gli alert, liste, dataclass `Config`), non
tramite un framework di dependency injection. `run_once` in `relay/main.py` è la sola funzione che
conosce l'ordine delle operazioni (leggi alert -> filtra nuovi -> notifica -> segna come visti ->
pota i risolti); i singoli client non si conoscono a vicenda. Idempotenza per design: ogni alert
NinjaOne ha un `uid` stabile riusato come chiave di deduplica in `SeenAlertsStore`, così un riavvio
del processo o un doppio polling non producono messaggi duplicati.

## Sicurezza applicativa

Autenticazione verso NinjaOne: OAuth2 client credentials (machine-to-machine), scope consigliato
`monitoring` (sola lettura), niente permessi di scrittura richiesti dal relay. Il token in memoria
non viene mai loggato; solo `expires_in` finisce nei log INFO.
Autenticazione verso Telegram: token del bot, mai loggato, passato solo nell'URL della richiesta
HTTPS a `api.telegram.org`.
Gestione segreti: tutte le credenziali (client secret NinjaOne, token bot Telegram) vivono
esclusivamente in `.env`, file ignorato da `.gitignore` e mai letto dall'agente (`settings.json`
lo nega esplicitamente); il repository è pubblico su GitHub, quindi `.env.example` documenta i
nomi delle variabili senza mai un valore reale.
Validazione input: il testo libero proveniente da NinjaOne (`message`, nome del device) viene
sempre passato per `html.escape` prima di essere inserito nel testo HTML del messaggio Telegram,
per evitare che un messaggio di alert contenente `<`/`>`/`&` rompa il parsing HTML lato Telegram o
inietti markup non voluto; verificato in `tests/test_relay.py::test_new_alerts_are_notified_and_html_escaped`.
Superficie esposta: nessuna. Il relay non apre porte in ascolto, non riceve richieste in ingresso;
comunica solo in uscita verso NinjaOne e Telegram via HTTPS, quindi non richiede firewall,
tunnel o IP pubblico anche se eseguito dietro NAT domestico/aziendale.
Resilienza: `main()` cattura ogni eccezione per singolo ciclo di polling e continua al giro
successivo, per non far morire il processo per un errore di rete transitorio; `TelegramClient`
gestisce esplicitamente il rate limit 429 con backoff su `retry_after`.

## Diagrammi

Nessun diagramma ancora prodotto: l'architettura è lineare (polling -> filtro -> notifica) e
descritta a sufficienza in "Flussi di codice" di `STACK.md`. Da aggiungere se il flusso si
complica (es. introduzione di una coda o di più sorgenti NinjaOne).
