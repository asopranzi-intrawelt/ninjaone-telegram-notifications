---
generated-from-commit: PENDING-FIRST-COMMIT
generated-from-branch: main
generated-date: 2026-07-16
covers-paths:
  - relay/**
  - tests/**
last-verified-commit: PENDING-FIRST-COMMIT
stato: in verifica
---

# Lavoro in corso

> La fonte di verità su cosa è fatto resta `memory/index.md` e il work-log, non le spunte di
> questo file. Ogni feature si descrive con lo schema fisso sotto, così il lavoro pendente è
> leggibile senza ricostruire il contesto da capo.

## Feature: relay notifiche NinjaOne -> Telegram

Cosa fa: interroga periodicamente (polling) gli alert attivi di NinjaOne via API OAuth2, filtra
per severity (solo alta criticità, endpoint Intrawelt, istanza single-tenant) e inoltra i nuovi
alert al gruppo Telegram `tech_intrawelt`, menzionando due utenti designati.

File da creare:

```
(nessuno oltre a quanto gia' creato sotto relay/ e tests/)
```

File da modificare:

```
(nessuno in sospeso lato codice; da compilare .env con le credenziali NinjaOne mancanti)
```

Definition of done:

- [x] Architettura scelta: polling (pull) invece di webhook, per evitare esposizione pubblica;
      Python, relay self-hosted (ADR-002)
- [x] Bot Telegram creato (`@intrawelt_ninjabot`) e aggiunto al gruppo `tech_intrawelt`
- [x] Chat ID del gruppo recuperato (`-5148194232`, gruppo semplice, niente Topic)
- [ ] App API NinjaOne creata (client id/secret, scope monitoring) e istanza/regione confermata
- [x] Relay implementato end-to-end e verificato con NinjaOne/Telegram mockati (7 test in
      `tests/test_relay.py`, tutti passati, inclusi filtro di severity ed escalation)
- [ ] Relay verificato contro le API reali di NinjaOne e Telegram (manca ancora l'app API
      NinjaOne)
- [x] Gestione segreti fuori dal repository pubblico (.env ignorato, .env.example tracciato)
- [x] Formato messaggio compatto con emoji di severity (ADR-003), niente priorita' ne' timestamp
      esplicito
- [x] Filtro di severity implementato (`NINJAONE_MIN_SEVERITIES`), lasciato vuoto in `.env` in
      attesa di calibrare i valori reali (vedi sotto)
- [x] Tag/menzione dei due utenti designati: Alessio Sopranzi (`418933222`) e Daniele Colò
      (`29491021`), entrambi ricavati da un loro messaggio nel gruppo via getUpdates

Domande aperte:

- Client ID/secret dell'app API NinjaOne e regione dell'istanza (eu/us/ca/us2/fed/oc)
- Valori reali di `severity` restituiti dall'istanza NinjaOne: da osservare nei log del primo
  avvio (senza filtro) prima di valorizzare `NINJAONE_MIN_SEVERITIES` (attualmente vuoto in
  `.env`; `CRITICAL,MAJOR` in `.env.example` è solo un valore presunto, non verificato)
- Dove far girare il relay in modo persistente: PC Windows locale (Task Scheduler) o VM Proxmox

## Riconciliazione

Ultima verifica: 2026-07-16 al commit PENDING-FIRST-COMMIT.
