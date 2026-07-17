# Lanciatore del relay NinjaOne -> Telegram per l'avvio automatico (Task Scheduler o
# cartella Esecuzione automatica). Si posiziona sulla radice del progetto, cosi' .env e
# data/seen_alerts.json vengono risolti correttamente, e accoda stdout/stderr del relay
# a data/relay.log, che e' ignorato da git.

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$logDir = Join-Path $projectRoot "data"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$logFile = Join-Path $logDir "relay.log"

# Rotazione elementare: sopra i 5 MB il log corrente diventa .old e si riparte da vuoto.
if ((Test-Path $logFile) -and ((Get-Item $logFile).Length -gt 5MB)) {
    Move-Item $logFile "$logFile.old" -Force
}

$python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $python) {
    Add-Content $logFile "$(Get-Date -Format s) ERRORE lanciatore: python non trovato nel PATH"
    exit 1
}

Add-Content $logFile "$(Get-Date -Format s) Lanciatore: avvio relay con $python"

# La redirezione la fa cmd, non PowerShell: PowerShell riscriverebbe l'output in UTF-16 e
# incarterebbe lo stderr (dove logga Python) in record d'errore. -u disabilita il buffering,
# cosi' il log su file resta aggiornato riga per riga.
& cmd /c "`"$python`" -u -m relay.main >> `"$logFile`" 2>&1"
exit $LASTEXITCODE
