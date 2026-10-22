# PeleAnálise · levanta MySQL (3307), servicio de IA (8000) y frontend Nuxt (3000).
# Uso:  .\start.ps1          -> inicia lo que no esté corriendo
#       .\start.ps1 -Stop    -> detiene los tres
param([switch]$Stop)

$Root     = $PSScriptRoot
$MysqlBin = "C:\Program Files\MySQL\MySQL Server 8.4\bin"
$MysqlDir = "C:\Users\richa\pele_mysql_data"
$Venv     = "C:\Users\richa\pele_venv\Scripts\python.exe"
$Logs     = Join-Path $Root "logs"
New-Item -ItemType Directory -Force $Logs | Out-Null

function Get-PortPid($port) {
  (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess
}

function Wait-Port($port, $name, $seconds) {
  for ($i = 0; $i -lt $seconds; $i++) {
    if (Get-PortPid $port) { Write-Host "  OK  $name -> puerto $port" -ForegroundColor Green; return $true }
    Start-Sleep 1
  }
  Write-Host "  FALLO  $name no respondió en el puerto $port (revisa $Logs)" -ForegroundColor Red
  return $false
}

if ($Stop) {
  foreach ($port in 3000, 8000, 3307) {
    $p = Get-PortPid $port
    if ($p) { Stop-Process -Id $p -Force; Write-Host "Detenido puerto $port (PID $p)" }
  }
  return
}

foreach ($f in @("$MysqlBin\mysqld.exe", $MysqlDir, $Venv)) {
  if (-not (Test-Path $f)) { Write-Host "No existe: $f" -ForegroundColor Red; return }
}

Write-Host "Iniciando PeleAnálise..." -ForegroundColor Cyan

# 1. MySQL
if (-not (Get-PortPid 3307)) {
  Start-Process "$MysqlBin\mysqld.exe" -ArgumentList "--no-defaults", "--datadir=$MysqlDir", "--port=3307", "--bind-address=127.0.0.1", "--mysqlx=OFF" `
    -RedirectStandardOutput "$Logs\mysql.log" -RedirectStandardError "$Logs\mysql.err" -WindowStyle Hidden
}
if (-not (Wait-Port 3307 "MySQL" 30)) { return }

# 2. Servicio de IA (FastAPI)
if (-not (Get-PortPid 8000)) {
  Start-Process $Venv -ArgumentList "-m", "uvicorn", "app.main:app", "--port", "8000" -WorkingDirectory "$Root\python-ai" `
    -RedirectStandardOutput "$Logs\ai.log" -RedirectStandardError "$Logs\ai.err" -WindowStyle Hidden
}
$ai = Wait-Port 8000 "Servicio de IA" 90

# 3. Frontend (Nuxt)
if (-not (Get-PortPid 3000)) {
  Start-Process "cmd.exe" -ArgumentList "/c", "npx nuxt dev --port 3000" -WorkingDirectory "$Root\frontend" `
    -RedirectStandardOutput "$Logs\nuxt.log" -RedirectStandardError "$Logs\nuxt.err" -WindowStyle Hidden
}
$web = Wait-Port 3000 "Frontend" 90

if ($ai -and $web) {
  Write-Host ""
  Write-Host "Listo:" -ForegroundColor Cyan
  Write-Host "  App        http://localhost:3000"
  Write-Host "  IA (docs)  http://localhost:8000/docs"
  Write-Host "  Login      admin@peleanalise.mx / Admin123!"
}
