# Registro delle decisioni architetturali

> Convenzione ADR-lite, append-only. Ogni decisione architetturale non ovvia entra come voce
> numerata con data, stato, contesto, decisione, motivazione e conseguenze. Una decisione non si
> cancella e non si riscrive: quando viene superata, si aggiunge una nuova voce che dichiara di
> superare la precedente e ne cita il numero. Le inferenze non confermate si marcano come da
> verificare e si promuovono a decisione solo quando una fonte le conferma.

## ADR-001 — Adozione del sistema di progetto portabile

Data: 2026-07-16
Stato: accettata
Contesto: il progetto necessita di uno stato interamente recuperabile da un clone e di
documentazione che resti allineata al codice senza rilettura integrale a ogni sessione.
Decisione: adottare il sistema descritto in `.claude/PROJECT-SYSTEM.md`, con motore di
riconciliazione ancorato ai commit e doppio livello documentale tracciato/ignorato.
Motivazione: persistenza strutturale su disco indipendente dalla sessione di chat, e controllo
umano sul versionamento.
Conseguenze: ogni passo significativo aggiorna schede, `last-verified-commit`, snapshot e
work-log; commit e push restano manuali.

## ADR-002 — Relay a polling (pull) invece di webhook (push), Python, self-hosted

Data: 2026-07-16
Stato: accettata
Contesto: NinjaOne non offre un'integrazione Telegram nativa; le opzioni emerse da una ricerca
dedicata (webhook NinjaOne, community Dojo, dev.to, Reddit, repository GitHub open source,
piattaforme no-code) erano tre: relay self-hosted su webhook, automazione no-code (n8n/Albato),
script PowerShell condition-triggered lato NinjaOne. Il relay doveva girare su un PC Windows
personale o su una VM Proxmox, entrambi tipicamente dietro NAT senza IP pubblico.
Decisione: relay self-hosted in Python, che interroga (pull) periodicamente `GET /v2/alerts`
sull'API NinjaOne (OAuth2 client credentials, scope `monitoring`) invece di ricevere un webhook
in ingresso, e inoltra i nuovi alert a un gruppo Telegram via `sendMessage`.
Motivazione: il modello pull non richiede alcuna esposizione pubblica (nessun tunnel, nessuna
porta aperta, nessun IP pubblico), a differenza del modello push che richiederebbe NinjaOne cloud
raggiungesse un endpoint esposto dal PC/VM locale. Per un progetto a due utenti la latenza del
polling (minuti) è accettabile. Python scelto per leggibilità e perché la sola dipendenza
necessaria (`requests`) è sufficiente, senza bisogno di framework web essendo il relay un processo
long-running, non un server.
Conseguenze: la deduplica degli alert già notificati è responsabilità del relay stesso (via UID
persistito in `data/seen_alerts.json`, ignorato da git), non di NinjaOne. Il relay non riceve
eventi in tempo reale: la tempestività dipende da `POLL_INTERVAL_SECONDS`. Endpoint e schema
`Alert` verificati contro lo spec OpenAPI ufficiale di NinjaOne
(`ninjaOne-API-core-resources.yaml`, reperito dal repository homotechsual/NinjaOne) e contro il
codice sorgente del modulo PowerShell corrispondente, non assunti dalla sola documentazione
prosa.

## ADR-003 — Filtro di severity, formato messaggio compatto, deduplica per uid+severity

Data: 2026-07-16
Stato: accettata
Contesto: l'istanza NinjaOne monitora solo endpoint Intrawelt (nessun altro cliente/tenant),
quindi nessun filtro per organizzazione è necessario. L'utente vuole pero' ricevere solo gli
alert ad alta criticita', non ogni alert attivo, e un messaggio piu' sintetico di quello iniziale
(niente priorita' ne' timestamp esplicito, un'unica emoji legata alla severity).
Decisione: aggiunta la variabile `NINJAONE_MIN_SEVERITIES` (elenco di severity ammesse,
`relay/config.py` e `relay/main.py:_passes_severity_filter`); riformattato il messaggio in
`relay/formatting.py` a due righe piu' le menzioni, con un'emoji scelta da `SEVERITY_EMOJI` in
base al campo `severity`. La chiave di deduplica in `relay/state.py` e' passata da solo `uid` a
`uid+severity` (funzione `make_key`), cosi' un alert che peggiora nel tempo restando sullo stesso
uid viene rivalutato dal filtro invece di restare bloccato alla prima severity osservata.
Motivazione: i valori esatti di `severity` restituiti dall'istanza NinjaOne reale non sono ancora
verificati, mancando ancora le credenziali dell'app API; forzare un default gia' filtrato
rischierebbe di bloccare silenziosamente tutti gli alert se i valori indovinati non corrispondono
a quelli reali. Il default operativo scelto e' quindi filtro vuoto (nessuna esclusione) al primo
avvio reale, con log esplicito delle severity osservate per calibrare `NINJAONE_MIN_SEVERITIES`
prima di restringere.
Conseguenze: finche' il filtro resta vuoto, il gruppo riceve tutti gli alert attivi; la
calibrazione e' un passo manuale successivo, tracciato in `context/deployment.md` e
`context/current-work.md`. La mappa emoji per severity sconosciute usa un simbolo neutro
(bianco) invece di un colore a caso, cosi' un valore non mappato si nota subito in chat.
