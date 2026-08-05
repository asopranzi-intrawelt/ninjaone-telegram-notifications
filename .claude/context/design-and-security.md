---
generated-from-commit: 91c9917
generated-from-branch: main
generated-date: 2026-07-16
covers-paths:
  - relay/**
last-verified-commit: ac34b7b
---

# Design e sicurezza applicativa

> Popolare leggendo il codice attuale. I diagrammi referenziati vivono in `diagrams/` in
> corrispondenza uno a uno con i componenti descritti (sezione 7).

## Paradigmi di software design

Un modulo per responsabilità (config, client NinjaOne, client Telegram, stato locale,
formattazione, orchestrazione), nessuna classe base astratta o plugin system: lo scambio tra i
moduli avviene passando oggetti semplici (dict per gli alert, liste, dataclass `Config`), non
tramite un framework di dependency injection. `run_once` in `relay/main.py` è la sola funzione che
conosce l'ordine delle operazioni (leggi alert e risolvine l'organizzazione -> filtra nuovi ->
notifica -> segna come visti -> pota i risolti); i singoli client non si conoscono a vicenda.
Idempotenza per design: ogni alert NinjaOne ha un `uid` stabile riusato come chiave di deduplica in
`SeenAlertsStore`, così un riavvio del processo o un doppio polling non producono messaggi
duplicati.

Fail-closed sul filtro per organizzazione, e scarto sempre osservabile. Poiche' l'organizzazione
non e' un campo dell'alert ma va risolta dal `deviceId` attraverso l'anagrafica dei device, esiste
il caso in cui la risoluzione non riesce, tipicamente un device aggiunto a NinjaOne dopo l'ultimo
aggiornamento della cache. In quel caso `_filter_by_organization` scarta l'alert invece di
ammetterlo, perche' ammetterlo significherebbe pubblicare in chat l'alert di un cliente diverso;
prima di concludere che un `deviceId` e' ignoto, `_select_alerts` forza pero' una rilettura
dell'anagrafica, cosi' il caso legittimo del device nuovo non viene perso. Ogni scarto lascia
traccia nei log, quelli di altre organizzazioni a livello INFO e quelli non risolvibili a livello
WARNING con l'elenco dei `deviceId`: la scelta e' deliberata e nasce dall'incidente descritto in
ADR-004, dove un filtro che scartava tutto in silenzio ha lasciato il gruppo Telegram muto per due
settimane senza che nulla nei log lo segnalasse.

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
Riservatezza fra clienti dell'MSP: l'app API vede tutte le organizzazioni gestite dall'MSP che
amministra l'istanza, non la sola Intrawelt, quindi il filtro per organizzazione non e' una
comodita' di rumore ma un controllo di riservatezza, ed e' il motivo per cui e' fail-closed e
applicato due volte, lato server con il device filter e lato client sulla mappa dei device
(vedi ADR-004). Un `NINJAONE_ORGANIZATION_IDS` vuoto disattiva il controllo e fa uscire in chat
gli alert di tutti i clienti dell'MSP: il relay lo segnala con un WARNING all'avvio, ma resta
una configurazione da non usare in produzione.
Validazione input: il testo libero proveniente da NinjaOne (`message`, `conditionName`, e in
generale ogni campo dell'alert riportato in chat) viene
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
