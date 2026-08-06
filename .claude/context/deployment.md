---
generated-from-commit: 91c9917
generated-from-branch: main
generated-date: 2026-07-16
covers-paths:
  - relay/**
  - requirements.txt
  - .env.example
last-verified-commit: ac34b7b
---

# Deployment

> Popolare leggendo la configurazione reale di infrastruttura e CI. Commit, push e deploy restano operazioni manuali dell'utente.

## Livelli

Nessun livello di staging: un solo processo long-running, o sul PC Windows di sviluppo o su una VM Proxmox, scelta ancora aperta (vedi `current-work.md`). Essendo un modello a polling in uscita, nessuna delle due opzioni richiede porte aperte, IP pubblico o domini: basta accesso in uscita a `eu.ninjarmm.com` (o l'host dell'istanza scelta) e `api.telegram.org` sulla porta 443.

## Comandi

Setup locale:

```
python -m venv .venv
.venv\Scripts\activate          (Windows)  /  source .venv/bin/activate   (Linux)
pip install -r requirements.txt
copy .env.example .env           (Windows)  /  cp .env.example .env       (Linux)
# compilare .env con le credenziali reali, mai committarlo
python -m relay.main
```

Avvio persistente su Windows, configurato e in esercizio: attivita' pianificata utente `NinjaOneTelegramRelay`, con trigger al logon e fino a tre riavvii in caso di crash, che esegue `tools/run-relay.ps1`. Il lanciatore si posiziona sulla radice del progetto, cosi' `.env` e `data/seen_alerts.json` si risolvono correttamente, e accoda stdout e stderr del relay a `data/relay.log`, ruotandolo in `.old` oltre i 5 MB. La redirezione la esegue `cmd` e non PowerShell, perche' PowerShell riscriverebbe l'output in UTF-16 e incarterebbe in record d'errore lo stderr, dove Python logga.

Riavvio del relay, procedura da seguire dopo ogni modifica a `.env` o al codice, dato che la configurazione si legge solo all'avvio. `Stop-ScheduledTask` da solo non basta: termina l'attivita' ma lascia vivo il processo Python, che il lanciatore ha staccato attraverso `cmd`, e il vecchio codice continua a girare mentre l'attivita' risulta ferma su Ready. Va quindi terminato anche il processo, individuandolo per riga di comando, prima di riavviare l'attivita'.

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*relay.main*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Stop-ScheduledTask -TaskName "NinjaOneTelegramRelay"
Start-ScheduledTask -TaskName "NinjaOneTelegramRelay"
```

La conferma che il riavvio sia andato a buon fine si legge in `data/relay.log`, dove devono comparire una riga `Lanciatore: avvio relay` con l'orario corrente e la riga `Relay avviato` con i filtri effettivamente in vigore; se quelle righe non compaiono, l'attivita' non e' ripartita.

Ripresa dopo un fermo prolungato: gli alert rimasti attivi durante il fermo sono tutti nuovi per lo stato locale e verrebbero notificati insieme al riavvio. Per assorbirli senza inondare il gruppo si esegue un solo giro silenzioso con `python -m relay.main --prime`, che li segna come gia' visti senza inviare nulla, e solo dopo si riavvia l'attivita' pianificata.

Rollback: nessuna migrazione né stato server-side oltre `data/seen_alerts.json`; tornare a una versione precedente equivale a un `git checkout` del codice e un riavvio del processo.

## Variabili d'ambiente e segreti

Elenco completo in `.env.example` (tracciato, senza valori). Le variabili richieste sono: `NINJAONE_INSTANCE`, `NINJAONE_CLIENT_ID`, `NINJAONE_CLIENT_SECRET`, `NINJAONE_SCOPE`, `NINJAONE_ORGANIZATION_IDS`, `NINJAONE_MIN_SEVERITIES`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_MESSAGE_THREAD_ID` (opzionale), `TELEGRAM_MENTION_USER_IDS`, `POLL_INTERVAL_SECONDS`, `STATE_FILE_PATH`. I valori reali vivono solo in `.env`, locale e ignorato da git (vedi `.gitignore` e `settings.json`, che nega esplicitamente la lettura di `.env`/`.env.*` all'agente).

## Provisioning delle credenziali

Il gruppo Telegram di destinazione è `tech_intrawelt`. Questa sezione è il runbook operativo di come si sono procurate, o si procureranno, le credenziali elencate sopra, cosi' che il procedimento sopravviva a un clone e non vada rifatto a memoria in una sessione futura.

Creazione del bot: da Telegram, conversazione con l'utente `@BotFather`, comando `/newbot`, scelta di un nome visualizzato e di uno username che termina per `bot`. La risposta di BotFather contiene il token, nella forma `<id numerico>:<stringa>`, da riportare in `TELEGRAM_BOT_TOKEN`. Il bot va poi aggiunto come membro del gruppo `tech_intrawelt` perche' possa scrivervi.

Chat ID del gruppo: il modo affidabile, indipendente dal fatto che il gruppo abbia uno username pubblico, e' inviare un messaggio qualunque nel gruppo dopo aver aggiunto il bot, poi chiamare `https://api.telegram.org/bot<TOKEN>/getUpdates` e leggere il campo `chat.id` del messaggio piu' recente; per un gruppo normale (non supergroup) il valore e' negativo, per una supergroup ha il prefisso `-100`. Il valore trovato va in `TELEGRAM_CHAT_ID`.

Topic del gruppo: da usare solo se `tech_intrawelt` e' una supergroup con la funzione Topic abilitata e si vuole indirizzare le notifiche a un topic specifico invece che al topic generale; il `message_thread_id` si legge dallo stesso payload di `getUpdates`, nel campo `message.message_thread_id` di un messaggio inviato in quel topic. Se non richiesto, la variabile `TELEGRAM_MESSAGE_THREAD_ID` resta vuota e il messaggio va nel topic generale del gruppo.

ID Telegram dei due utenti da menzionare: si ottengono facendo scrivere a ciascun utente un messaggio al bot `@userinfobot`, che risponde con il proprio ID numerico; i due valori, separati da virgola, vanno in `TELEGRAM_MENTION_USER_IDS`.

App API NinjaOne: dalla console NinjaOne, sezione Amministrazione, poi App, poi API, sezione Client app IDs, creazione di una nuova applicazione con concessione (grant) di tipo client credentials e scope `monitoring`. La console mostra client ID e client secret, da riportare rispettivamente in `NINJAONE_CLIENT_ID` e `NINJAONE_CLIENT_SECRET`; la regione dell'istanza (dominio con cui si accede alla console, es. `eu.ninjarmm.com`) va riportata in `NINJAONE_INSTANCE` come uno tra `eu`, `us`, `ca`, `us2`, `fed`, `oc`. Se l'istanza e' brandizzata white-label, come nel caso di questo progetto, la sigla di regione non esiste e in `NINJAONE_INSTANCE` va l'URL https completo della console, che il codice usa verbatim come base URL dell'API.

ID dell'organizzazione da filtrare: si legge da `GET /v2/organizations` sull'istanza, autenticati con la stessa app API, cercando nella risposta la voce il cui `name` corrisponde all'organizzazione desiderata e prendendone il campo `id`. Il valore, o l'elenco separato da virgole se le organizzazioni sono piu' di una, va in `NINJAONE_ORGANIZATION_IDS`; il valore reale in uso vive solo in `.env`, non qui.

Valori ammessi per il filtro di severity: l'enumerazione ufficiale dello spec OpenAPI, campo *Policy condition severity*, e' `NONE`, `MINOR`, `MODERATE`, `MAJOR`, `CRITICAL`, e tutti e cinque sono stati osservati su questa istanza. `NINJAONE_MIN_SEVERITIES` non e' una soglia nonostante il nome: il confronto e' per uguaglianza esatta sui valori elencati, quindi per avere l'alta criticita' vanno indicati entrambi i valori che la compongono, e una variabile vuota lascia passare tutto.

Stato del provisioning, aggiornato man mano che i passi si completano:

| Credenziale | Variabile | Stato |
|---|---|---|
| Bot Telegram | `TELEGRAM_BOT_TOKEN` | fatto (`@intrawelt_ninjabot`) |
| Chat ID gruppo `tech_intrawelt` | `TELEGRAM_CHAT_ID` | fatto (`-5148194232`, gruppo semplice) |
| Topic ID (se applicabile) | `TELEGRAM_MESSAGE_THREAD_ID` | non applicabile, `tech_intrawelt` non e' una supergroup |
| ID dei due utenti da menzionare | `TELEGRAM_MENTION_USER_IDS` | fatto (Alessio Sopranzi `418933222`, Daniele Colò `29491021`) |
| App API NinjaOne | `NINJAONE_CLIENT_ID` / `NINJAONE_CLIENT_SECRET` | fatto (machine-to-machine, client credentials, scope `monitoring`) |
| Istanza NinjaOne | `NINJAONE_INSTANCE` | fatto (istanza brandizzata white-label su infrastruttura EU, URL https completo) |
| Filtro severity | `NINJAONE_MIN_SEVERITIES` | fatto, calibrato il 2026-08-05 su `CRITICAL,MAJOR` dopo aver osservato i valori reali (vedi ADR-004) |
| Filtro organizzazione | `NINJAONE_ORGANIZATION_IDS` | fatto, id letto da `GET /v2/organizations`; valore solo in `.env` |

Filtro per organizzazione: necessario, a differenza di quanto assunto in precedenza. L'istanza NinjaOne (`puntoinformatica.rmmservice.eu`) e' gestita dall'MSP esterno Punto Informatica (Via Andrea Costa, Porto San Giorgio), che segue Intrawelt tramite Daniele Colò; l'assunzione iniziale era che, essendo l'accesso di Alessio Sopranzi alla console scoped alla sola organizzazione Intrawelt, ogni alert attivo fosse gia' di Intrawelt per definizione. In produzione si e' osservato che l'app API OAuth2 usata dal relay non eredita lo scoping della singola login utente in console: i permessi di un'app client-credentials sono un asse indipendente e su questa istanza vedono tutte le organizzazioni gestite da Punto Informatica, non la sola Intrawelt. Il relay applica quindi un filtro esplicito, popolato dalla lista di ID in `NINJAONE_ORGANIZATION_IDS`; se la variabile e' vuota il relay logga un avviso e non filtra nulla.

Come il filtro risolve l'organizzazione, corretto il 2026-08-05. La prima implementazione leggeva `organizationId` da un oggetto `device` annidato nell'Alert, campo che l'API non restituisce: l'unico riferimento al dispositivo presente nel payload di `GET /v2/alerts` e' `deviceId`, e l'organizzazione va risolta attraverso `GET /v2/devices`, dove ogni device porta il proprio `organizationId`. Il risultato di quell'errore e' stato un filtro che scartava in silenzio ogni alert, con il gruppo Telegram muto dal 20 luglio al 5 agosto; il dettaglio dell'incidente e della correzione sta in ADR-004. L'implementazione attuale chiede il filtro anche al server, con il device filter `df` su `/v2/alerts` (sintassi `org=<id>` per una sola organizzazione, `org in (<id>,<id>)` per piu' di una, mentre `org=<id>,<id>` viene rifiutata con `InvalidFilterException`), e lo riapplica lato client sulla mappa `deviceId -> organizationId` messa in cache per 900 secondi, scartando in modo tracciato cio' che non riesce ad attribuire.
