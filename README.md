# ninjaone-telegram-notifications

Relay che interroga periodicamente (polling) gli alert attivi di NinjaOne RMM[^1] e li inoltra al
gruppo Telegram `tech_intrawelt`, menzionando due utenti designati.

---

## Stack

Python 3.10+, dipendenza unica `requests`. Nessun server web: un processo long-running che
interroga l'API[^2] NinjaOne a intervalli regolari, nessun webhook in ingresso e nessuna
esposizione pubblica necessaria. Vedi `.claude/context/STACK.md` per il dettaglio dei moduli.

---

## Come funziona

Il relay si autentica su NinjaOne via OAuth2[^3] client credentials, scope `monitoring` (sola
lettura), interroga `GET /v2/alerts` ogni `POLL_INTERVAL_SECONDS`, e per ogni alert non ancora
notificato invia un messaggio HTML[^4] al gruppo Telegram configurato tramite l'API Bot,
menzionando i due utenti configurati. Lo stato degli alert già notificati è persistito localmente
per evitare duplicati tra un polling e il successivo. Il procedimento dettagliato per procurarsi
bot, chat ID e credenziali NinjaOne è tracciato in `.claude/context/deployment.md`, sezione
"Provisioning delle credenziali".

## Setup

```
python -m venv .venv
.venv\Scripts\activate          (Windows)  /  source .venv/bin/activate   (Linux)
pip install -r requirements.txt
copy .env.example .env           (Windows)  /  cp .env.example .env       (Linux)
# compilare .env: credenziali NinjaOne, token bot Telegram, chat ID, ID utenti da menzionare
python -m relay.main
```

Test:

```
python -m unittest discover tests -v
```

---

## Stato

- [x] Architettura scelta (relay Python a polling, self-hosted, nessuna esposizione pubblica)
- [x] Relay implementato e verificato con NinjaOne/Telegram mockati (filtro di severity incluso)
- [x] Bot Telegram creato e aggiunto al gruppo `tech_intrawelt`
- [ ] App API NinjaOne creata
- [ ] Verificato contro le API reali con un alert vero

---

## Riferimenti

Le fonti sotto sono il risultato di una ricerca dedicata su cosa esiste già per collegare
NinjaOne a Telegram, condotta prima di scegliere l'architettura (vedi `memory/decisions.md`,
ADR-002). Sono divise tra le fonti usate come riferimento primario per scrivere il codice, quindi
verificate direttamente, e le fonti di prior art consultate per la scelta architetturale ma non
incorporate nel codice.

Fonti primarie, verificate direttamente contro il codice sorgente o lo spec, non assunte dalla
sola prosa documentale:

- [NinjaOne Public API, reference](https://app.ninjarmm.com/apidocs-beta/): pagina indice dell'API pubblica NinjaOne
- [ninjaOne-API-core-resources.yaml](https://raw.githubusercontent.com/homotechsual/NinjaOne/main/ninjaOne-API-core-resources.yaml): spec OpenAPI completa, fonte dei path `/v2/alerts` e dello schema `Alert` usati in `relay/ninjaone_client.py`
- [homotechsual/NinjaOne](https://github.com/homotechsual/NinjaOne): modulo PowerShell community, il più maturo tra quelli censiti; `Connect-NinjaOne.ps1` ha confermato l'endpoint token `/ws/oauth/token` e la forma della richiesta client credentials
- [docs.homotechsual.dev](https://docs.homotechsual.dev/modules/ninjaone/): documentazione del modulo sopra
- [Telegram Bot API](https://core.telegram.org/bots/api): riferimento ufficiale, fonte di `sendMessage`, `message_thread_id`, formati di `parse_mode`

Fonti consultate per la scelta architetturale (ADR-002), non incorporate direttamente nel codice:

- [NinjaOne, canali di notifica](https://www.ninjaone.com/docs/new-to-ninjaone/alerting-and-notifications/endpoint-notification-channels-alerts/): canali nativi (email, SMS, Slack, Teams, PagerDuty, webhook generico), nessun canale Telegram nativo
- [NinjaOne, panoramica webhook Activity](https://app.ninjarmm.com/apidocs-beta/core-resources/articles/webhooks/overview): meccanismo push alternativo al polling, scartato per l'esposizione pubblica richiesta
- [NinjaOne, flusso client credentials](https://app.ninjarmm.com/apidocs-beta/authorization/flows/client-credentials-flow): conferma discorsiva del flusso OAuth2 usato
- [NinjaOne, condizioni delle policy](https://www.ninjaone.com/docs/endpoint-management/policies/policy-conditions/): meccanismo alla base dell'opzione "script PowerShell diretto", scartata in ADR-002
- [provectio/ninjaone-teamswebhook](https://github.com/provectio/ninjaone-teamswebhook): relay Go verso Teams, miglior analogo strutturato per un ricevitore di webhook NinjaOne
- [redbaron2k7/ninjacord-webhook-translator](https://github.com/redbaron2k7/ninjacord-webhook-translator): relay PHP verso Discord, stessa forma esatta del problema
- [janw/alertmanager-telegram](https://github.com/janw/alertmanager-telegram): relay Prometheus Alertmanager verso Telegram, riferimento per coda e formattazione
- [ak9999/ninjaonepy](https://github.com/ak9999/ninjaonepy): wrapper Python community per l'API NinjaOne, non usato direttamente ma censito come alternativa
- [n8n, nodo Telegram](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.telegram): opzione no-code scartata in ADR-002 per mantenere il progetto autonomo
- [Albato, connettore NinjaOne-Telegram](https://albato.com/connect/ninjaone-with-telegramprivate): unica piattaforma che pubblicizza un connettore diretto NinjaOne-Telegram, scartata perché introduce una terza parte a pagamento

[^1]: RMM, Remote Monitoring and Management: software di monitoraggio e gestione remota di endpoint, usato dagli MSP (Managed Service Provider) per sorvegliare i dispositivi dei clienti.
[^2]: API, Application Programming Interface: interfaccia con cui due programmi si scambiano dati, qui l'API pubblica di NinjaOne.
[^3]: OAuth2, Open Authorization versione 2: protocollo standard per l'autorizzazione delegata, qui nella variante client credentials, pensata per l'autenticazione da macchina a macchina senza un utente umano nel flusso.
[^4]: HTML, HyperText Markup Language: qui usato come `parse_mode` di Telegram per formattare il testo del messaggio (grassetto, link).
