# Work-log

> Append-only, in ordine cronologico inverso (la voce più recente in alto). Ogni passo
> significativo di codice e ogni intervento manuale rilevante lascia una voce con data, file
> toccati, motivo e commit di riferimento. Qui confluisce anche il log di riconciliazione dei
> documenti `.docx`, con il nome del documento sorgente e l'esito, così la data di allineamento
> sopravvive a un clone.

## 2026-08-05 — Ancoraggio dei PENDING-FIRST-COMMIT e riconciliazione delle schede

Commit: ac34b7b
File toccati: `context/STACK.md`, `context/design-and-security.md`, `context/deployment.md`,
`context/dev-testing.md`, `context/current-work.md`, `context/roadmap.md`, `memory/index.md`,
`memory/decisions.md` (ADR-004).
Motivo: tutte le schede portavano ancora il segnaposto `PENDING-FIRST-COMMIT`, creato in
greenfield prima che il repository avesse un commit. Il segnaposto e' stato ancorato a `91c9917`,
il primo commit, che e' quello che materializza lo stato descritto dalle schede, e non
direttamente a HEAD: ancorare a HEAD avrebbe dichiarato verificato anche cio' che i commit del
filtro per organizzazione hanno cambiato, mascherando il drift da correggere. Sul delta
`91c9917..HEAD` risultavano stale cinque schede su sei, aggiornate con edit chirurgici sulle sole
sezioni impattate, e `last-verified-commit` portato a `ac34b7b`. Due correzioni riguardano drift
anteriore al primo commit, che il confronto fra commit non puo' mostrare: il loader `.env` nativo
e il supporto agli URL brandizzati in `STACK.md`, e l'avvio automatico in `deployment.md`, che era
descritto come non ancora configurato mentre e' in esercizio dal 17 luglio. `roadmap.md` e' stata
ancorata ma resta a contenuto segnaposto. Anche le cinque voci storiche di questo work-log, che
riportavano `Commit: PENDING-FIRST-COMMIT`, sono state ancorate a `91c9917`, il commit in cui quel
lavoro e' effettivamente entrato: e' la risoluzione di un segnaposto, non la riscrittura di una
voce. La sezione di `deployment.md` che descriveva il filtro
come basato sul campo `organizationId` di un oggetto `device` annidato nell'Alert e' stata
riscritta, perche' quel campo non esiste ed era la fonte documentale dell'errore.

## 2026-08-05 — Ripristinato il filtro per organizzazione, calibrata la severity

Commit: ac34b7b
File toccati: `relay/ninjaone_client.py` (helper `_get` con retry su 401, `get_active_alerts` con
device filter `df`, `get_device_organizations` con cache a 900 secondi,
`device_filter_expression`), `relay/main.py` (`_select_alerts`, `_filter_by_organization`, logging
degli scarti, flag `--prime`), `tests/test_relay.py` (fixture riscritte sul payload reale, da 12 a
23 test), `.env.example` (`NINJAONE_ORGANIZATION_IDS`), `.env` (filtro severity su
`CRITICAL,MAJOR`, modificato dall'utente).
Motivo: il gruppo Telegram era muto dal 20 luglio. Il filtro per organizzazione introdotto quel
giorno leggeva `alert["device"]["organizationId"]`, campo inesistente nel payload reale di
`GET /v2/alerts`, che porta solo `deviceId`: ogni alert veniva scartato in silenzio, con il
processo vivo, il token rinnovato ogni ora e `data/seen_alerts.json` rimasto lista vuota. Le
fixture dei test contenevano l'oggetto `device` inventato, quindi la suite era verde. Diagnosi
condotta sull'API reale in sola lettura, correzione descritta in ADR-004, verifica con 23 test
verdi piu' un dry run reale che seleziona 46 alert su 77 attivi, tutti dell'organizzazione
attesa, e un messaggio di test consegnato nel gruppo su autorizzazione dell'utente. Sono emersi
due fatti operativi: `Stop-ScheduledTask` non termina il processo Python staccato da `cmd`, quindi
il primo riavvio aveva lasciato in esecuzione il codice vecchio, e ogni modifica a `.env` richiede
un riavvio perche' la configurazione si legge solo all'avvio. Entrambi documentati in
`context/deployment.md`. Relay riavviato alle 15:47 con `filtro severity=['CRITICAL', 'MAJOR']` e
filtro per organizzazione attivo.
Resta da fare: risoluzione del nome del device nei messaggi (oggi `device #<id>`), troncamento dei
messaggi da event log Windows e Veeam, ed eventuale spostamento su VM Proxmox per la copertura
24/7.

## 2026-07-16 — Secondo utente da menzionare recuperato

Commit: 91c9917
File toccati: `.env`, `context/deployment.md`, `context/current-work.md`.
Motivo: Daniele Colò (@danielecolo) ha scritto nel gruppo `tech_intrawelt`, ID Telegram
`29491021` letto via `getUpdates` con lo stesso meccanismo usato per Alessio Sopranzi.
`TELEGRAM_MENTION_USER_IDS` ora ha entrambi gli utenti. Il provisioning Telegram e' completo:
resta solo l'app API NinjaOne (client id/secret, regione) e la calibrazione del filtro di
severity sui valori reali.

## 2026-07-16 — Provisioning Telegram completato, filtro di severity e formato compatto (ADR-003)

Commit: 91c9917
File toccati: `relay/formatting.py` (formato a due righe con emoji di severity, niente priorita'
ne' timestamp esplicito), `relay/config.py` (nuovo campo `min_severities`), `relay/main.py`
(filtro `_passes_severity_filter`, log delle severity osservate per calibrazione), `relay/state.py`
(deduplica per `uid+severity` via `make_key`, non piu' solo `uid`), `tests/test_relay.py`
(riscritto: 7 test, inclusi filtro di severity ed escalation dello stesso alert), `.env`/
`.env.example`, `context/deployment.md` (tabella di stato provisioning aggiornata, filtro
organizzazione dichiarato non necessario), `context/current-work.md`, `memory/decisions.md`
(ADR-003).
Motivo: bot Telegram creato (`@intrawelt_ninjabot`), aggiunto al gruppo `tech_intrawelt`
(gruppo semplice, chat ID `-5148194232` recuperato via `getUpdates` dopo aver disattivato la
privacy mode del bot), primo utente da menzionare noto (Alessio Sopranzi, `418933222`) ricavato
dallo stesso messaggio invece che da `@userinfobot`. Confermato che l'istanza NinjaOne e'
single-tenant (solo endpoint Intrawelt): nessun filtro per organizzazione necessario, solo
filtro di severity. Il filtro e' implementato ma lasciato vuoto in `.env` perche' i valori reali
di `severity` di questa istanza NinjaOne non sono ancora verificati (mancano le credenziali
dell'app API): la calibrazione avverra' osservando i log del primo avvio reale.
Resta da fare: ID Telegram del secondo utente, app API NinjaOne (client id/secret, regione),
calibrazione del filtro di severity, verifica end-to-end contro le API reali.

## 2026-07-16 — Tracciata la guida di provisioning e la bibliografia delle fonti

Commit: 91c9917
File toccati: `context/deployment.md` (nuova sezione "Provisioning delle credenziali" con il
runbook passo-passo per bot Telegram, chat ID, topic, ID utenti, app API NinjaOne, e una tabella
di stato per credenziale), `README.md` (sezione Riferimenti espansa in bibliografia completa,
divisa tra fonti primarie verificate direttamente e fonti di prior art consultate per la scelta
architetturale, footnote per gli acronimi secondo `rules/interaction-style.md`).
Motivo: il gruppo Telegram di destinazione è stato confermato (`tech_intrawelt`), e l'utente ha
chiesto di tracciare in documentazione tutti i passaggi di provisioning man mano che si
completano, insieme a tutte le fonti della ricerca iniziale. Il provisioning è in corso: bot
Telegram in fase di creazione (Step 1 della guida), le altre credenziali ancora da procurare.

## 2026-07-16 — Prima implementazione del relay NinjaOne -> Telegram

Commit: 91c9917
File toccati: `relay/` (config, ninjaone_client, telegram_client, state, formatting, main),
`tests/test_relay.py`, `requirements.txt`, `.env.example`, `.gitignore` (aggiunta `data/`),
`README.md`, schede `context/STACK.md`, `design-and-security.md`, `deployment.md`,
`current-work.md`.
Motivo: implementare ADR-002 (relay Python a polling, self-hosted). Endpoint OAuth2
(`/ws/oauth/token`) e alert (`/v2/alerts`, schema `Alert`) verificati contro lo spec OpenAPI
ufficiale NinjaOne e il codice sorgente del modulo PowerShell homotechsual/NinjaOne, non assunti
dalla ricerca sommaria. Verificato end-to-end con NinjaOne/Telegram mockati: 4 test in
`tests/test_relay.py`, tutti passati (nuovo alert notificato, escaping HTML, campi mancanti,
deduplica al polling successivo, pruning di un alert risolto). Non ancora verificato contro le
API reali: mancano credenziali NinjaOne e Telegram effettive (bot, chat ID, ID utenti da
menzionare).

## 2026-07-16 — Inizializzazione del sistema di progetto

Commit: 91c9917
File toccati: anatomia di `.claude`, `CLAUDE.md`, `.gitignore`, schede di `context/`, identità git
locale (alias `github-corp`), remote `origin` verso `asopranzi-intrawelt/ninjaone-telegram-notifications`
(repository pubblico).
Motivo: installazione del sistema portabile di contesto, documentazione e version control
descritto in `.claude/PROJECT-SYSTEM.md`, allineando il progetto a `E:\template-claude-developing`.
Schede create con struttura e frontmatter, da popolare nelle sessioni successive quando
l'architettura del relay NinjaOne -> Telegram viene decisa e implementata. Completata in parallelo
una ricerca completa su soluzioni esistenti (webhook nativi NinjaOne, community Dojo, dev.to,
Reddit, repository GitHub open source, piattaforme di integrazione) per informare la decisione
architetturale.
