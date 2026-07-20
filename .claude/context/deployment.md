---
generated-from-commit: PENDING-FIRST-COMMIT
generated-from-branch: main
generated-date: 2026-07-16
covers-paths:
  - relay/**
  - requirements.txt
  - .env.example
last-verified-commit: PENDING-FIRST-COMMIT
---

# Deployment

> Popolare leggendo la configurazione reale di infrastruttura e CI. Commit, push e deploy restano
> operazioni manuali dell'utente.

## Livelli

Nessun livello di staging: un solo processo long-running, o sul PC Windows di sviluppo o su una
VM Proxmox, scelta ancora aperta (vedi `current-work.md`). Essendo un modello a polling in uscita,
nessuna delle due opzioni richiede porte aperte, IP pubblico o domini: basta accesso in uscita a
`eu.ninjarmm.com` (o l'host dell'istanza scelta) e `api.telegram.org` sulla porta 443.

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

Avvio persistente su Windows (opzione, non ancora configurata): Task Scheduler con un'azione che
esegue `pythonw.exe -m relay.main` dalla cartella del progetto con l'ambiente virtuale attivo, ad
esempio al login o all'avvio del sistema.

Rollback: nessuna migrazione né stato server-side oltre `data/seen_alerts.json`; tornare a una
versione precedente equivale a un `git checkout` del codice e un riavvio del processo.

## Variabili d'ambiente e segreti

Elenco completo in `.env.example` (tracciato, senza valori). Le variabili richieste sono:
`NINJAONE_INSTANCE`, `NINJAONE_CLIENT_ID`, `NINJAONE_CLIENT_SECRET`, `NINJAONE_SCOPE`,
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_MESSAGE_THREAD_ID` (opzionale),
`TELEGRAM_MENTION_USER_IDS`, `POLL_INTERVAL_SECONDS`, `STATE_FILE_PATH`. I valori reali vivono
solo in `.env`, locale e ignorato da git (vedi `.gitignore` e `settings.json`, che nega
esplicitamente la lettura di `.env`/`.env.*` all'agente).

## Provisioning delle credenziali

Il gruppo Telegram di destinazione è `tech_intrawelt`. Questa sezione è il runbook operativo di
come si sono procurate, o si procureranno, le credenziali elencate sopra, cosi' che il
procedimento sopravviva a un clone e non vada rifatto a memoria in una sessione futura.

Creazione del bot: da Telegram, conversazione con l'utente `@BotFather`, comando `/newbot`,
scelta di un nome visualizzato e di uno username che termina per `bot`. La risposta di BotFather
contiene il token, nella forma `<id numerico>:<stringa>`, da riportare in `TELEGRAM_BOT_TOKEN`.
Il bot va poi aggiunto come membro del gruppo `tech_intrawelt` perche' possa scrivervi.

Chat ID del gruppo: il modo affidabile, indipendente dal fatto che il gruppo abbia uno username
pubblico, e' inviare un messaggio qualunque nel gruppo dopo aver aggiunto il bot, poi chiamare
`https://api.telegram.org/bot<TOKEN>/getUpdates` e leggere il campo `chat.id` del messaggio piu'
recente; per un gruppo normale (non supergroup) il valore e' negativo, per una supergroup ha il
prefisso `-100`. Il valore trovato va in `TELEGRAM_CHAT_ID`.

Topic del gruppo: da usare solo se `tech_intrawelt` e' una supergroup con la funzione Topic
abilitata e si vuole indirizzare le notifiche a un topic specifico invece che al topic generale;
il `message_thread_id` si legge dallo stesso payload di `getUpdates`, nel campo
`message.message_thread_id` di un messaggio inviato in quel topic. Se non richiesto, la variabile
`TELEGRAM_MESSAGE_THREAD_ID` resta vuota e il messaggio va nel topic generale del gruppo.

ID Telegram dei due utenti da menzionare: si ottengono facendo scrivere a ciascun utente un
messaggio al bot `@userinfobot`, che risponde con il proprio ID numerico; i due valori, separati
da virgola, vanno in `TELEGRAM_MENTION_USER_IDS`.

App API NinjaOne: dalla console NinjaOne, sezione Amministrazione, poi App, poi API, sezione
Client app IDs, creazione di una nuova applicazione con concessione (grant) di tipo client
credentials e scope `monitoring`. La console mostra client ID e client secret, da riportare
rispettivamente in `NINJAONE_CLIENT_ID` e `NINJAONE_CLIENT_SECRET`; la regione dell'istanza
(dominio con cui si accede alla console, es. `eu.ninjarmm.com`) va riportata in
`NINJAONE_INSTANCE` come uno tra `eu`, `us`, `ca`, `us2`, `fed`, `oc`.

Stato del provisioning, aggiornato man mano che i passi si completano:

| Credenziale | Variabile | Stato |
|---|---|---|
| Bot Telegram | `TELEGRAM_BOT_TOKEN` | fatto (`@intrawelt_ninjabot`) |
| Chat ID gruppo `tech_intrawelt` | `TELEGRAM_CHAT_ID` | fatto (`-5148194232`, gruppo semplice) |
| Topic ID (se applicabile) | `TELEGRAM_MESSAGE_THREAD_ID` | non applicabile, `tech_intrawelt` non e' una supergroup |
| ID dei due utenti da menzionare | `TELEGRAM_MENTION_USER_IDS` | fatto (Alessio Sopranzi `418933222`, Daniele Colò `29491021`) |
| App API NinjaOne | `NINJAONE_CLIENT_ID` / `NINJAONE_CLIENT_SECRET` | da fare |
| Regione istanza NinjaOne | `NINJAONE_INSTANCE` | da fare |
| Filtro severity | `NINJAONE_MIN_SEVERITIES` | in attesa di calibrazione: lasciato vuoto finche' non si osservano i valori reali nei log (vedi ADR-003) |
| Filtro organizzazione | `NINJAONE_ORGANIZATION_IDS` | da fare: serve l'id numerico dell'organizzazione Intrawelt, recuperabile con una chiamata a `GET /v2/organizations` sull'istanza |

Filtro per organizzazione: necessario, a differenza di quanto assunto in precedenza. L'istanza NinjaOne (`puntoinformatica.rmmservice.eu`) e' gestita dall'MSP esterno Punto Informatica (Via Andrea Costa, Porto San Giorgio), che segue Intrawelt tramite Daniele Colò; l'assunzione iniziale era che, essendo l'accesso di Alessio Sopranzi alla console scoped alla sola organizzazione Intrawelt, ogni alert attivo fosse gia' di Intrawelt per definizione. In produzione si e' osservato che l'app API OAuth2 usata dal relay non eredita lo scoping della singola login utente in console: i permessi di un'app client-credentials sono un asse indipendente e su questa istanza vedono tutte le organizzazioni gestite da Punto Informatica, non la sola Intrawelt. Il relay applica quindi un filtro esplicito lato codice sul campo `organizationId` dell'oggetto `device` annidato in ogni Alert (`relay/main.py:_belongs_to_organizations`), verificato contro lo schema ufficiale NinjaOne v2/alerts, popolato dalla lista di ID in `NINJAONE_ORGANIZATION_IDS`; se la variabile e' vuota il relay logga un avviso e non filtra nulla, comportamento identico al bug osservato.
