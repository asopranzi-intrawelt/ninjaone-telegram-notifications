---
generated-from-commit: 91c9917
generated-from-branch: main
generated-date: 2026-07-16
covers-paths:
  - tests/**
last-verified-commit: ac34b7b
---

# Test di sviluppo

> Popolare leggendo la configurazione reale dei test. La checklist operativa locale dei test manuali vive invece in `_notes/TEST-CHECKLIST.md`, ignorata da git.

## Test runner e comandi

`unittest` di libreria standard, nessuna dipendenza di test aggiuntiva. Comando dalla radice del progetto:

```
python -m unittest discover tests -v
```

Copertura attuale: `tests/test_relay.py`, un solo file, 23 test. Sul percorso completo di `run_once` stanno la notifica di un alert nuovo, l'escaping HTML, i campi mancanti, la deduplica al polling successivo, il pruning di un alert risolto con notifica del nuovo, il filtro di severity con il caso di escalation dello stesso `uid`, il filtro per organizzazione nelle sue quattro varianti (device filter effettivamente inviato al server, alert di un'altra organizzazione scartato, alert di device non risolvibile scartato, indice dei device riletto quando compare un device nuovo) e il priming con `notify=False`. A parte stanno i test di `device_filter_expression`, di `Config.from_env` e del loader `.env`. Nessun test gira contro le API reali di NinjaOne o Telegram.

## Rotte e dati mockate

`relay.ninjaone_client.requests.post`/`.get` e `relay.telegram_client.requests.post` sono sostituiti via `unittest.mock.patch` con funzioni fake che simulano: la risposta del token OAuth2 (`/ws/oauth/token`), la lista alert (`/v2/alerts`), l'anagrafica dei device (`/v2/devices`) e la risposta 200 di `sendMessage` di Telegram. Il fake di `GET` smista per URL e registra i parametri di query, cosi' un test puo' verificare che il device filter sia stato davvero chiesto al server; le risposte di `/v2/devices` sono una sequenza, cosi' un test puo' simulare un'anagrafica che si aggiorna tra un giro e l'altro. Nessun server HTTP reale viene avviato.

Le fixture riproducono il payload realmente restituito dall'istanza, non lo schema dedotto dalla documentazione. Il punto e' costato un bug in produzione, descritto in ADR-004: le fixture precedenti contenevano un oggetto `device` annidato con `organizationId`, che l'API non restituisce, e i test passavano verdi mentre in produzione il filtro scartava ogni alert. La regola che ne discende e' che un campo usato per una decisione di filtro va osservato una volta sull'istanza reale prima di finire in una fixture.

## Verifica contro l'API reale

I test non toccano le API vere, quindi la verifica end-to-end resta un passo manuale. Lo script locale `_notes/dry-run-filter.py`, ignorato da git e quindi non presente in un clone, esegue la selezione degli alert con la configurazione reale di `.env` e stampa quanti alert passano, quali organizzazioni sono rappresentate e un'anteprima dei messaggi, senza inviare nulla a Telegram e senza scrivere lo stato. Si lancia dalla radice con `PYTHONPATH=.` e serve dopo ogni modifica al filtro; per ricrearlo bastano `load_dotenv`, `Config.from_env`, un `NinjaOneClient` e una chiamata a `relay.main._select_alerts`.

## Hook e controlli di qualità

Nessun lint o type-check configurato al momento (nessun `pyproject.toml`/`ruff`/`mypy`). Prima di un commit: eseguire i test sopra e `python -m py_compile relay/*.py` come controllo sintattico minimo.
