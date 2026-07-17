# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di
> riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto,
> non le spunte del diario.

## Stato

```
Branch attivo:        main
Commit di riferimento: PENDING-FIRST-COMMIT
Data snapshot:        2026-07-16
```

## Stato di verifica delle schede

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | PENDING-FIRST-COMMIT | popolata con lo stack reale |
| design-and-security.md | PENDING-FIRST-COMMIT | popolata con lo stack reale |
| deployment.md | PENDING-FIRST-COMMIT | popolata con lo stack reale |
| dev-testing.md | PENDING-FIRST-COMMIT | popolata con lo stack reale |
| current-work.md | PENDING-FIRST-COMMIT | popolata, in verifica |
| roadmap.md | PENDING-FIRST-COMMIT | struttura creata, da popolare |

## Punto di ripresa

Prima implementazione del relay completa e verificata con NinjaOne/Telegram mockati (vedi
`current-work.md`). Prossimo passo: raccogliere le credenziali reali (app API NinjaOne, bot
Telegram, chat ID del gruppo, ID utenti da menzionare), compilare `.env`, far girare il relay
contro le API vere e osservare il primo alert reale arrivare su Telegram. Dopo il primo commit
utente, eseguire la skill `sync-context` per sostituire ogni `PENDING-FIRST-COMMIT` con l'hash di
HEAD.
