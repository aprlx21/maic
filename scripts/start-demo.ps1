param([int]$Port = 8765)
$ErrorActionPreference = 'Stop'
$project = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $project
$python = Join-Path $project '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Create .venv and install the project first; see README.md.' }
if (-not (Test-Path -LiteralPath (Join-Path $project 'frontend\dist\index.html'))) {
    throw 'Build the frontend first: npm --prefix frontend run build'
}
$env:PYTHONUTF8 = '1'
if (-not $env:MAIC_SLIDE_FONT) { $env:MAIC_SLIDE_FONT = 'Arial' }
$logs = Join-Path $project 'data\logs'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$address = "http://127.0.0.1:$Port"
$online = $false
try { $null = Invoke-RestMethod "$address/api/config" -TimeoutSec 3; $online = $true } catch {}
if (-not $online) {
    Start-Process -FilePath $python -ArgumentList @('-m','uvicorn','app.main:app','--host','127.0.0.1','--port',"$Port") -WorkingDirectory $project -WindowStyle Hidden -RedirectStandardOutput "$logs\web.out.log" -RedirectStandardError "$logs\web.err.log" | Out-Null
}
$worker = Get-CimInstance Win32_Process | Where-Object {
    $_.ExecutablePath -eq $python -and $_.CommandLine -match '-m\s+app\.worker(?:\s|$)'
}
if (-not $worker) {
    Start-Process -FilePath $python -ArgumentList @('-m','app.worker') -WorkingDirectory $project -WindowStyle Hidden -RedirectStandardOutput "$logs\worker.out.log" -RedirectStandardError "$logs\worker.err.log" | Out-Null
}
Write-Output "MAIC demo: $address"
Write-Output "Logs: $logs"
