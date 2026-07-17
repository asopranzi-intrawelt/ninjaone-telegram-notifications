---
generated-from-commit: PENDING-FIRST-COMMIT
generated-from-branch: main
generated-date: 2026-07-16
covers-paths:
  - tests/**
last-verified-commit: PENDING-FIRST-COMMIT
---

# Test di sviluppo

> Popolare leggendo la configurazione reale dei test. La checklist operativa locale dei test
> manuali vive invece in `_notes/TEST-CHECKLIST.md`, ignorata da git.

## Test runner e comandi

`unittest` di libreria standard, nessuna dipendenza di test aggiuntiva. Comando dalla radice del
progetto:

```
python -m unittest discover tests -v
```

Copertura attuale: `tests/test_relay.py`, un solo file, 4 test end-to-end sul percorso completo
`run_once` (nuovo alert notificato, escaping HTML, campi mancanti, deduplica al polling
successivo, pruning di un alert risolto con notifica del nuovo). Nessun test gira contro le API
reali di NinjaOne o Telegram.

## Rotte e dati mockate

`relay.ninjaone_client.requests.post`/`.get` e `relay.telegram_client.requests.post` sono
sostituiti via `unittest.mock.patch` con funzioni fake che simulano: la risposta del token OAuth2
(`/ws/oauth/token`), la lista alert (`/v2/alerts`, con payload conforme allo schema `Alert`
verificato sullo spec OpenAPI ufficiale di NinjaOne), e la risposta 200 di `sendMessage` di
Telegram. Nessun server HTTP reale viene avviato.

## Hook e controlli di qualità

Nessun lint o type-check configurato al momento (nessun `pyproject.toml`/`ruff`/`mypy`). Prima di
un commit: eseguire i test sopra e `python -m py_compile relay/*.py` come controllo sintattico
minimo.
