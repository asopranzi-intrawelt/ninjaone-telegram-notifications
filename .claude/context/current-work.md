---
generated-from-commit: 91c9917
generated-from-branch: main
generated-date: 2026-07-16
covers-paths:
  - relay/**
  - tests/**
last-verified-commit: ac34b7b
stato: in esercizio
---

# Lavoro in corso

> La fonte di verità su cosa è fatto resta `memory/index.md` e il work-log, non le spunte di questo file. Ogni feature si descrive con lo schema fisso sotto, così il lavoro pendente è leggibile senza ricostruire il contesto da capo.

## Feature: relay notifiche NinjaOne -> Telegram

Cosa fa: interroga periodicamente (polling) gli alert attivi di NinjaOne via API OAuth2, tiene solo quelli dei dispositivi dell'organizzazione Intrawelt (l'istanza e' multi-tenant, gestita da un MSP esterno) e con severity `CRITICAL` o `MAJOR`, e inoltra i nuovi alert al gruppo Telegram `tech_intrawelt`, menzionando due utenti designati. In esercizio dal 2026-07-17 sul PC Windows, via attivita' pianificata `NinjaOneTelegramRelay`.

File da creare:

```
(nessuno oltre a quanto gia' creato sotto relay/ e tests/)
```

File da modificare:

```
(nessuno in sospeso lato codice; .env compilato e calibrato, relay in esercizio)
```

Definition of done:

- [x] Architettura scelta: polling (pull) invece di webhook, per evitare esposizione pubblica; Python, relay self-hosted (ADR-002)
- [x] Bot Telegram creato (`@intrawelt_ninjabot`) e aggiunto al gruppo `tech_intrawelt`
- [x] Chat ID del gruppo recuperato (`-5148194232`, gruppo semplice, niente Topic)
- [x] App API NinjaOne creata (client id/secret, scope monitoring) e istanza confermata (dominio brandizzato white-label, non una sigla di regione)
- [x] Relay implementato end-to-end e verificato con NinjaOne/Telegram mockati (23 test in `tests/test_relay.py`, tutti passati, inclusi filtro di severity, escalation, filtro per organizzazione e priming)
- [x] Relay verificato contro le API reali di NinjaOne e Telegram: alert reali arrivati nel gruppo dal 2026-07-17, e catena riverificata capo a fondo il 2026-08-05 (dry run in sola lettura sull'API piu' messaggio di test consegnato nel gruppo)
- [x] Gestione segreti fuori dal repository pubblico (.env ignorato, .env.example tracciato)
- [x] Formato messaggio compatto con emoji di severity (ADR-003), niente priorita' ne' timestamp esplicito
- [x] Filtro di severity implementato (`NINJAONE_MIN_SEVERITIES`) e calibrato il 2026-08-05 su `CRITICAL,MAJOR` dopo aver osservato i cinque valori reali dell'istanza
- [x] Filtro per organizzazione funzionante: l'organizzazione si risolve dal `deviceId` via `GET /v2/devices`, non da un campo dell'alert, ed e' chiesta anche al server con il device filter `df` (ADR-004)
- [x] Avvio automatico in esercizio: attivita' pianificata `NinjaOneTelegramRelay` che lancia `tools/run-relay.ps1`, log in `data/relay.log` con rotazione a 5 MB
- [x] Tag/menzione dei due utenti designati: Alessio Sopranzi (`418933222`) e Daniele Colò (`29491021`), entrambi ricavati da un loro messaggio nel gruppo via getUpdates

Domande aperte:

- Nome del device nei messaggi: oggi il titolo mostra il ripiego `device #<id>`, perche' l'alert non porta un nome di dispositivo. L'indice dei device ora in memoria contiene `systemName`, quindi la risoluzione e' una modifica di poche righe, non ancora fatta.
- Leggibilita' dei messaggi da event log Windows e Veeam, che sono muri di testo: troncare il campo `message` tenendo condizione e device in testa. Direzione proposta, non decisa.
- Dove far girare il relay in modo persistente a copertura 24/7: oggi PC Windows locale, quindi nessuna notifica quando la macchina e' spenta; l'alternativa e' una VM Proxmox (nota in radice, articolo foisfabio.it su Proxmox e Telegram).

## Riconciliazione

Ultima verifica: 2026-08-05 al commit ac34b7b.
