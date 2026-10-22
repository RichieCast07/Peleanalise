# PeleAnalise - prepara (si hace falta) y levanta MySQL (3307), servicio de IA (8000) y frontend (3000).
#
# Uso:   powershell -ExecutionPolicy Bypass -File .\start.ps1          -> instala lo que falte y arranca todo
#        powershell -ExecutionPolicy Bypass -File .\start.ps1 -Stop    -> detiene los tres servicios
#        ... -Seed                                                     -> vuelve a cargar los usuarios iniciales
#
# Requisitos: MySQL 8 (winget install Oracle.MySQL), Node 20+, Python 3.11 o 3.12 (no 3.13+: TensorFlow).
# Todo se guarda fuera del repo, en %USERPROFILE%\.peleanalise (datos de MySQL y entorno de Python).
param([switch]$Stop, [switch]$Seed)

$ErrorActionPreference = "Continue"
$Root   = $PSScriptRoot
$Front  = Join-Path $Root "frontend"
$AiDir  = Join-Path $Root "python-ai"
$Logs   = Join-Path $Root "logs"
$Store  = Join-Path $env:USERPROFILE ".peleanalise"
New-Item -ItemType Directory -Force $Logs, $Store | Out-Null

function Info($m) { Write-Host $m -ForegroundColor Cyan }
function Ok($m)   { Write-Host "  OK  $m" -ForegroundColor Green }
function Fail($m) { Write-Host "  ERROR  $m" -ForegroundColor Red }

function Get-PortPid($port) {
  (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess
}

function Wait-Port($port, $name, $seconds) {
  for ($i = 0; $i -lt $seconds; $i++) {
    if (Get-PortPid $port) { Ok "$name -> puerto $port"; return $true }
    Start-Sleep 1
  }
  Fail "$name no respondio en el puerto $port (revisa los registros en $Logs)"
  return $false
}

if ($Stop) {
  foreach ($port in 3000, 8000, 3307) {
    $p = Get-PortPid $port
    if ($p) { Stop-Process -Id $p -Force; Write-Host "Detenido puerto $port (PID $p)" }
  }
  return
}

Info "Preparando PeleAnalise..."

# ---------- 1. MySQL ----------
$mysqld = Get-ChildItem "C:\Program Files\MySQL\MySQL Server *\bin\mysqld.exe" -ErrorAction SilentlyContinue |
          Sort-Object FullName | Select-Object -Last 1
if (-not $mysqld) {
  Fail "No se encontro MySQL. Instalalo con:  winget install Oracle.MySQL   y vuelve a ejecutar este script."
  return
}
$MysqlBin = $mysqld.DirectoryName
$mysqlExe = Join-Path $MysqlBin "mysql.exe"

# Reutiliza la carpeta de datos de versiones anteriores si existe
$legacyData = Join-Path $env:USERPROFILE "pele_mysql_data"
$MysqlData  = if (Test-Path $legacyData) { $legacyData } else { Join-Path $Store "mysql" }
$freshDb    = $false

if (-not (Test-Path (Join-Path $MysqlData "mysql"))) {
  Info "Inicializando datos de MySQL en $MysqlData ..."
  New-Item -ItemType Directory -Force $MysqlData | Out-Null
  & $mysqld.FullName --no-defaults --initialize-insecure --datadir="$MysqlData" 2>&1 | Out-Null
  $freshDb = $true
}

if (-not (Get-PortPid 3307)) {
  Start-Process $mysqld.FullName -ArgumentList "--no-defaults", "--datadir=$MysqlData", "--port=3307", "--bind-address=127.0.0.1", "--mysqlx=OFF" `
    -RedirectStandardOutput "$Logs\mysql.log" -RedirectStandardError "$Logs\mysql.err" -WindowStyle Hidden
}
if (-not (Wait-Port 3307 "MySQL" 40)) { return }

# Crea la base y el usuario si todavia no existen
$hasDb = & $mysqlExe -h 127.0.0.1 -P 3307 -u root -N -e "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name='peleanalise';" 2>$null
if ($hasDb -ne "1") {
  Info "Creando base de datos peleanalise ..."
  cmd /c "`"$mysqlExe`" -h 127.0.0.1 -P 3307 -u root < `"$Front\prisma\init.sql`""
  cmd /c "`"$mysqlExe`" -h 127.0.0.1 -P 3307 -u root < `"$Front\prisma\create_user.sql`""
  $freshDb = $true
}

# ---------- 2. Entorno de Python (servicio de IA) ----------
$legacyVenv = Join-Path $env:USERPROFILE "pele_venv"
$Venv       = if (Test-Path "$legacyVenv\Scripts\python.exe") { $legacyVenv } else { Join-Path $Store "venv" }
$VenvPy     = Join-Path $Venv "Scripts\python.exe"

if (-not (Test-Path $VenvPy)) {
  $launcher = $null
  foreach ($v in "3.12", "3.11") {
    & py "-$v" --version 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $launcher = $v; break }
  }
  if (-not $launcher) {
    Fail "Se necesita Python 3.11 o 3.12 (TensorFlow no funciona con 3.13+). Instala con:  winget install Python.Python.3.12"
    return
  }
  Info "Creando entorno de Python $launcher e instalando dependencias (tarda varios minutos, TensorFlow pesa ~1 GB)..."
  & py "-$launcher" -m venv $Venv
  & $VenvPy -m pip install --quiet --upgrade pip
  & $VenvPy -m pip install --quiet -r (Join-Path $AiDir "requirements.txt")
  if ($LASTEXITCODE -ne 0) { Fail "Fallo la instalacion de dependencias de Python."; return }
}

# ---------- 3. Frontend ----------
$envFile = Join-Path $Front ".env"
if (-not (Test-Path $envFile)) {
  Info "Creando frontend\.env ..."
  function New-Secret { -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 48 | ForEach-Object { [char]$_ }) }
  @(
    'DATABASE_URL="mysql://cesar:cesar123@127.0.0.1:3307/peleanalise"',
    "JWT_SECRET=`"$(New-Secret)`"",
    "JWT_REFRESH_SECRET=`"$(New-Secret)`"",
    'PYTHON_AI_URL="http://localhost:8000"',
    'NODE_ENV="development"'
  ) | Set-Content -Path $envFile -Encoding ASCII
}

if (-not (Test-Path (Join-Path $Front "node_modules\nuxt"))) {
  Info "Instalando dependencias de Node (npm install) ..."
  Push-Location $Front; cmd /c "npm install --no-audit --no-fund"; Pop-Location
}
if (-not (Test-Path (Join-Path $Front "node_modules\.prisma\client\index.js"))) {
  Push-Location $Front; cmd /c "npx prisma generate"; Pop-Location
}
if ($freshDb -or $Seed) {
  Info "Cargando usuarios iniciales ..."
  Push-Location $Front; cmd /c "npx tsx prisma/seed.ts"; Pop-Location
}

# ---------- 4. Servicios ----------
if (-not (Get-PortPid 8000)) {
  Start-Process $VenvPy -ArgumentList "-m", "uvicorn", "app.main:app", "--port", "8000" -WorkingDirectory $AiDir `
    -RedirectStandardOutput "$Logs\ai.log" -RedirectStandardError "$Logs\ai.err" -WindowStyle Hidden
}
$ai = Wait-Port 8000 "Servicio de IA" 120

if (-not (Get-PortPid 3000)) {
  Start-Process "cmd.exe" -ArgumentList "/c", "npx nuxt dev --port 3000" -WorkingDirectory $Front `
    -RedirectStandardOutput "$Logs\nuxt.log" -RedirectStandardError "$Logs\nuxt.err" -WindowStyle Hidden
}
$web = Wait-Port 3000 "Frontend" 120

if ($ai -and $web) {
  Write-Host ""
  Info "Listo:"
  Write-Host "  App        http://localhost:3000"
  Write-Host "  IA (docs)  http://localhost:8000/docs"
  Write-Host "  Login      admin@peleanalise.mx / Admin123!"
  $health = try { Invoke-RestMethod http://localhost:8000/health -TimeoutSec 5 } catch { $null }
  if ($health -and -not $health.model_loaded) {
    Write-Host ""
    Write-Host "  AVISO: no hay modelo entrenado (python-ai\models\melanoma_classifier.keras)." -ForegroundColor Yellow
    Write-Host "         El analisis funciona pero las probabilidades son de DEMOSTRACION." -ForegroundColor Yellow
  }
}
