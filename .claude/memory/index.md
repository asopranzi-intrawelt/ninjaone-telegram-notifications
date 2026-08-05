# Snapshot di sincronizzazione

> Da leggere per primo a inizio sessione. Fotografa lo stato del progetto al commit di
> riferimento e mappa ogni scheda al suo stato di verifica. È la fonte di verità su cosa è fatto,
> non le spunte del diario.

## Stato

```
Branch attivo:        main
Commit di riferimento: ac34b7b
Data snapshot:        2026-08-05
```

## Stato di verifica delle schede

| Scheda | last-verified | Stato |
|---|---|---|
| STACK.md | ac34b7b | allineata al codice in esercizio |
| design-and-security.md | ac34b7b | allineata al codice in esercizio |
| deployment.md | ac34b7b | allineata, include il runbook di riavvio |
| dev-testing.md | ac34b7b | allineata, 23 test |
| current-work.md | ac34b7b | allineata, feature in esercizio |
| roadmap.md | ac34b7b | ancorata, contenuto ancora a segnaposto |

## Punto di ripresa

Relay in esercizio e verificato capo a fondo il 2026-08-05: filtra gli alert della sola
organizzazione Intrawelt risolvendone l'appartenenza dal `deviceId` (ADR-004) e le sole severity
`CRITICAL` e `MAJOR`, girando sul PC Windows via attivita' pianificata `NinjaOneTelegramRelay`.
Nessun lavoro di codice in sospeso. I tre punti aperti, tutti facoltativi, sono elencati in
`current-work.md`: risolvere il nome del device nei messaggi al posto del ripiego `device #<id>`,
troncare i messaggi da event log Windows e Veeam, e valutare lo spostamento su VM Proxmox per la
copertura 24/7. Da popolare, quando serve, il contenuto di `roadmap.md`.
