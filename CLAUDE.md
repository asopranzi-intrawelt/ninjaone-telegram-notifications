# ninjaone-telegram-notifications

> Istruzioni di team, versionate. Questo file è l'indice del progetto: indicizza i soli file
> satellite tracciati e descrive la procedura di ripresa. Le preferenze personali vivono in
> `CLAUDE.local.md`, ignorato da git, non qui.

## Cos'è questo progetto

Relay che inoltra le notifiche/alert di NinjaOne RMM verso Telegram, in un gruppo dedicato,
notificando due utenti nominati. Repository pubblico su GitHub: massima attenzione a non
tracciare mai token, credenziali o informazioni aziendali/clienti nei file versionati.

## Procedura di ripresa in una sessione nuova

Lo stato del progetto è interamente recuperabile su disco. All'inizio di una sessione si segue
questo percorso fisso. Si legge per primo `.claude/memory/index.md`, che dà branch, commit di
riferimento, stato di verifica di ogni scheda e punto di ripresa. Si legge poi
`.claude/context/current-work.md` se c'è una feature attiva, per sapere cosa è in lavorazione e
quali sono i TODO e i limiti d'ambiente. Si invoca la skill `sync-context` per verificare il
drift tra schede e codice, e si leggono solo le schede pertinenti al task, mai tutte insieme. Il
work-log `.claude/memory/progress.md` e il registro `.claude/memory/decisions.md` forniscono la
storia e le decisioni quando servono. Il materiale grezzo sotto `_notes/` si apre solo per
verificare un requisito originale. Per una ripresa rapida esiste, quando presente,
`_notes/RESUME-PROMPT.md`, privato e ignorato: riporta lo stato raggiunto e un prompt pronto da
incollare. Va aggiornato alla fine di ogni sessione con il punto in cui si e arrivati, mentre lo
stato canonico resta `.claude/memory/index.md`.

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

Regole modulari caricate su necessità, sotto `.claude/rules/`, e skill richiamabili, sotto
`.claude/skills/`. Lo standard di sistema completo è in `.claude/PROJECT-SYSTEM.md`.

## Apprendimenti recenti

```
- [2026-07-16] Ricerca completa NinjaOne->Telegram completata: NinjaOne non ha integrazione
  Telegram nativa ma supporta webhook generico (notification channel) e Activity Webhook via
  API; miglior prior art open source: provectio/ninjaone-teamswebhook (Go) e
  redbaron2k7/ninjacord-webhook-translator (PHP), entrambi adattabili sostituendo il target
  Discord/Teams con Telegram Bot API.
- [2026-07-16] Decisione architetturale presa (ADR-002): relay Python a polling anziche' webhook,
  per evitare esposizione pubblica del PC/VM che lo ospita. Endpoint OAuth2 e schema Alert
  verificati contro lo spec OpenAPI ufficiale NinjaOne (reperito nel repository GitHub
  homotechsual/NinjaOne, file ninjaOne-API-core-resources.yaml) e il codice sorgente del modulo
  PowerShell corrispondente, non assunti dalla sola documentazione prosa. Prima implementazione
  completa sotto relay/, verificata con 4 test end-to-end in tests/test_relay.py (NinjaOne e
  Telegram mockati via unittest.mock).
```

## Vincoli di team

Le operazioni di `git add`, commit e push restano sempre manuali dell'utente: l'agente prepara i
file, non committa. L'identità git è impostata a livello locale del repo secondo
`.claude/rules/git-identity-and-repo.md` (alias `github-corp`). Lo stile di documentazione e di
interazione è quello di `.claude/rules/interaction-style.md`. Claude non scrive autonomamente nei
file di memoria e di contesto: li aggiorna solo su richiesta esplicita, così il versionamento
resta sotto controllo umano.
