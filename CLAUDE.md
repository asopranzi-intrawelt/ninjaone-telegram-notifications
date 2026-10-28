# ninjaone-telegram-notifications

> Istruzioni di team, versionate. Questo file è l'indice del progetto: indicizza i soli file satellite tracciati e descrive la procedura di ripresa. Le preferenze personali vivono in `CLAUDE.local.md`, ignorato da git, non qui.

## Cos'è questo progetto

Relay che inoltra le notifiche/alert di NinjaOne RMM verso Telegram, in un gruppo dedicato, notificando due utenti nominati. Repository pubblico su GitHub: massima attenzione a non tracciare mai token, credenziali o informazioni aziendali/clienti nei file versionati.

## Procedura di ripresa in una sessione nuova

Lo stato del progetto è interamente recuperabile su disco. All'inizio di una sessione si segue questo percorso fisso. Si legge per primo `.claude/memory/index.md`, che dà branch, commit di riferimento, stato di verifica di ogni scheda e punto di ripresa. Si legge poi `.claude/context/current-work.md` se c'è una feature attiva, per sapere cosa è in lavorazione e quali sono i TODO e i limiti d'ambiente. Si invoca la skill `sync-context` per verificare il drift tra schede e codice, e si leggono solo le schede pertinenti al task, mai tutte insieme. Il work-log `.claude/memory/progress.md` e il registro `.claude/memory/decisions.md` forniscono la storia e le decisioni quando servono. Il materiale grezzo sotto `_notes/` si apre solo per verificare un requisito originale. Per una ripresa rapida esiste, quando presente, `_notes/RESUME-PROMPT.md`, privato e ignorato: riporta lo stato raggiunto e un prompt pronto da incollare. Va aggiornato alla fine di ogni sessione con il punto in cui si e arrivati, mentre lo stato canonico resta `.claude/memory/index.md`.

## Indice dei file satellite tracciati

Memoria e meta-stato, sotto `.claude/memory/`, letti sempre a inizio sessione.

```
.claude/memory/index.md       snapshot e tabella di sincronizzazione, da leggere per primo
.claude/memory/progress.md    work-log append-only di passi e riconciliazioni
.claude/memory/decisions.md   registro ADR-lite delle decisioni architetturali
```

Schede tecniche, sotto `.claude/context/`, con frontmatter di riconciliazione.

```
.claude/context/STACK.md                stack, flussi di codice, ruolo architetturale dei file
.claude/context/design-and-security.md  paradigmi di design e sicurezza applicativa
.claude/context/deployment.md           livelli test e produzione, hosting, comandi
.claude/context/dev-testing.md          test di sviluppo, runner, rotte mockate, hook
.claude/context/current-work.md         feature attiva, definition of done, domande aperte
.claude/context/roadmap.md              direzione e priorità
```

Regole modulari caricate su necessità, sotto `.claude/rules/`, e skill richiamabili, sotto `.claude/skills/`. Lo standard di sistema completo è in `.claude/PROJECT-SYSTEM.md`.

Norme caricate su richiesta, una riga per situazione con le parole con cui si presenta, così che il caricamento non dipenda dal ricordare che la norma esista.

- `git worktree list` mostra più di un albero, se ne crea o se ne rimuove uno, si deve decidere da dove leggere la memoria versionata: skill `alberi-di-lavoro`.
- Va prodotto, modificato o convertito un artefatto visivo o documentale, cioè un documento, una presentazione, un PDF, un'immagine, un'animazione, un audio o un impaginato, oppure si sta per scrivere uno script o installare una libreria per farlo: skill `craft-apps`, che prima verifica in locale le applicazioni Craft installate e le usa senza rete né token.
- Un recupero web fallisce con 403 o con una pagina di verifica anti-bot, la fonte sta su Reddit o su Discord, serve la trascrizione di un video, si sta per annotare una fonte non letta: skill `fonti-non-recuperabili`.
- Si imposta o si verifica user.name e user.email, si collega o si cambia il remoto o l'alias SSH, si inizializza un repository, un push fallisce per permessi, `/status` mostra un account Claude diverso da quello atteso, si autentica o si usa `gh`: skill `identita-git`.
- Si scrive o si valuta una prova automatica, si chiude un difetto, una verifica manuale smentisce una suite verde, si sta per dichiarare completo un intervento il cui scopo era un effetto misurabile, si progetta il controllo in esercizio di un servizio, si indaga un guasto e si deve stabilire che cosa dicono davvero le prove raccolte: skill `prove-che-misurano`.
- Si inizializza o si allinea il progetto, oppure cambia il modo in cui si prova e si rilascia, e va deciso come separare test e produzione: skill `separazione-ambienti`.

## Apprendimenti recenti

```
- [2026-07-16] Ricerca completa NinjaOne->Telegram completata: NinjaOne non ha integrazione
  Telegram nativa ma supporta webhook generico (notification channel) e Activity Webhook via
  API; miglior prior art open source: provectio/ninjaone-teamswebhook (Go) e
  redbaron2k7/ninjacord-webhook-translator (PHP), entrambi adattabili sostituendo il target
  Discord/Teams con Telegram Bot API.
- [2026-08-05] L'oggetto Alert di NinjaOne (GET /v2/alerts) NON contiene un oggetto device
  annidato: porta solo deviceId, e l'organizzazione va risolta con GET /v2/devices. Il filtro che
  assumeva alert["device"]["organizationId"] scartava ogni alert in silenzio e ha tenuto muto il
  gruppo Telegram dal 20 luglio al 5 agosto, con i test verdi perche' le fixture contenevano il
  campo inventato (ADR-004). Un campo usato per filtrare va osservato una volta sull'istanza reale
  prima di finire in una fixture: lo spec OpenAPI descrive lo schema, non cosa l'endpoint popola.
- [2026-07-16] Decisione architetturale presa (ADR-002): relay Python a polling anziche' webhook,
  per evitare esposizione pubblica del PC/VM che lo ospita. Endpoint OAuth2 e schema Alert
  verificati contro lo spec OpenAPI ufficiale NinjaOne (reperito nel repository GitHub
  homotechsual/NinjaOne, file ninjaOne-API-core-resources.yaml) e il codice sorgente del modulo
  PowerShell corrispondente, non assunti dalla sola documentazione prosa. Prima implementazione
  completa sotto relay/, verificata con 4 test end-to-end in tests/test_relay.py (NinjaOne e
  Telegram mockati via unittest.mock).
```

## Vincoli di team

Le operazioni di `git add`, commit e push restano sempre manuali dell'utente: l'agente prepara i file, non committa. L'identità git è impostata a livello locale del repo secondo `.claude/rules/git-identity-and-repo.md` (alias `github-corp`). Lo stile di documentazione e di interazione è quello di `.claude/rules/interaction-style.md`. Claude non scrive autonomamente nei file di memoria e di contesto: li aggiorna solo su richiesta esplicita, così il versionamento resta sotto controllo umano.
