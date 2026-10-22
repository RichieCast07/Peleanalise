#!/bin/bash

set -e

CYAN="\033[0;36m"
MAGENTA="\033[0;35m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RESET="\033[0m"

echo ""
echo -e "${CYAN}╔══════════════════════════════════════╗${RESET}"
echo -e "${CYAN}║       PeleAnálise — Dev Server       ║${RESET}"
echo -e "${CYAN}╚══════════════════════════════════════╝${RESET}"
echo ""

# ── 1. .env ────────────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
  echo -e "${YELLOW}⚙  .env no encontrado → creando desde .env.example...${RESET}"
  cp .env.example .env
  echo -e "${GREEN}✓  .env creado. Edítalo con tus credenciales antes de continuar.${RESET}"
  echo ""
  read -p "   Presiona Enter cuando hayas configurado el .env (Ctrl+C para salir): "
fi

set -a
source .env
set +a
echo -e "${GREEN}✓  .env cargado${RESET}"

# ── 2. Base de datos ───────────────────────────────────────────────────────────
echo ""
DB_USER=$(echo "$DATABASE_URL" | sed -E 's|mysql://([^:]+):.*|\1|')
DB_PASS=$(echo "$DATABASE_URL" | sed -E 's|mysql://[^:]+:([^@]+)@.*|\1|')
DB_HOST=$(echo "$DATABASE_URL" | sed -E 's|mysql://[^@]+@([^:/]+).*|\1|')
DB_PORT=$(echo "$DATABASE_URL" | sed -E 's|mysql://[^@]+@[^:]+:([0-9]+)/.*|\1|')
DB_NAME=$(echo "$DATABASE_URL" | sed -E 's|.*/([^?]+).*|\1|')

[ -z "$DB_PORT" ] || [ "$DB_PORT" = "$DATABASE_URL" ] && DB_PORT="3306"

echo -e "${YELLOW}🗄  Verificando base de datos '${DB_NAME}'...${RESET}"
if mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" -e "USE \`${DB_NAME}\`;" 2>/dev/null; then
  echo -e "${GREEN}✓  Base de datos '${DB_NAME}' OK${RESET}"
else
  echo -e "${YELLOW}   Creando base de datos '${DB_NAME}'...${RESET}"
  mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" \
    -e "CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null
  echo -e "${GREEN}✓  Base de datos '${DB_NAME}' creada${RESET}"
fi

# ── 3. Dependencias Node ───────────────────────────────────────────────────────
echo ""
if [ ! -d node_modules ]; then
  echo -e "${YELLOW}📦 Instalando dependencias Node...${RESET}"
  npm install
  echo -e "${GREEN}✓  Dependencias Node instaladas${RESET}"
else
  echo -e "${GREEN}✓  node_modules OK${RESET}"
fi

# ── 4. Prisma: generar cliente y sincronizar tablas ────────────────────────────
echo ""
if [ ! -d node_modules/.prisma/client ]; then
  echo -e "${YELLOW}🔧 Generando cliente Prisma...${RESET}"
  npx prisma generate
fi

echo -e "${YELLOW}🗄  Sincronizando tablas con Prisma (db push)...${RESET}"
npx prisma db push --accept-data-loss 2>&1 | grep -v "^$" | tail -5
echo -e "${GREEN}✓  Tablas sincronizadas${RESET}"

# ── 5. Seed: solo si users está vacía ─────────────────────────────────────────
echo ""
USER_COUNT=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" \
  -se "SELECT COUNT(*) FROM \`${DB_NAME}\`.users;" 2>/dev/null || echo "0")

if [ "$USER_COUNT" = "0" ]; then
  echo -e "${YELLOW}🌱 Ejecutando seed (usuarios iniciales)...${RESET}"
  npx tsx prisma/seed.ts
  echo -e "${GREEN}✓  Seed completado${RESET}"
else
  echo -e "${GREEN}✓  Seed omitido (ya hay datos)${RESET}"
fi

# ── 6. Python: entorno virtual ────────────────────────────────────────────────
echo ""
VENV_DIR="../python-ai/venv"

# TensorFlow/OpenCV requieren Python 3.11 o 3.12 — buscar versión compatible
PYTHON_BIN=""
for candidate in python3.12 python3.11; do
  if command -v "$candidate" &>/dev/null; then
    PYTHON_BIN=$(command -v "$candidate")
    break
  fi
done

if [ -z "$PYTHON_BIN" ]; then
  echo -e "${YELLOW}🐍 Python 3.11/3.12 no encontrado → instalando python@3.11 con Homebrew...${RESET}"
  brew install python@3.11
  PYTHON_BIN=$(command -v python3.11)
fi

PYTHON_VER=$("$PYTHON_BIN" --version 2>&1)
echo -e "${GREEN}✓  Usando $PYTHON_VER${RESET}"

# Recrear venv si fue creado con Python 3.14
if [ -d "$VENV_DIR" ]; then
  VENV_VER=$("$VENV_DIR/bin/python" --version 2>&1 | grep -oE '3\.[0-9]+' | head -1)
  if [ "$VENV_VER" = "3.14" ] || [ "$VENV_VER" = "3.13" ]; then
    echo -e "${YELLOW}🐍 venv incompatible ($VENV_VER) → recreando con $PYTHON_VER...${RESET}"
    rm -rf "$VENV_DIR"
  fi
fi

if [ ! -d "$VENV_DIR" ]; then
  echo -e "${YELLOW}🐍 Creando entorno virtual Python...${RESET}"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
  echo -e "${GREEN}✓  Entorno virtual creado${RESET}"
fi

if ! "$VENV_DIR/bin/python" -c "import uvicorn" 2>/dev/null; then
  echo -e "${YELLOW}🐍 Instalando dependencias Python...${RESET}"
  "$VENV_DIR/bin/pip" install --upgrade pip --quiet
  "$VENV_DIR/bin/pip" install -r ../python-ai/requirements.txt
  echo -e "${GREEN}✓  Dependencias Python instaladas${RESET}"
else
  echo -e "${GREEN}✓  Dependencias Python OK${RESET}"
fi

# ── 7. Arrancar servidores ─────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}🚀 Iniciando servidores...${RESET}"
echo -e "   ${CYAN}Nuxt   →${RESET} http://localhost:3000"
echo -e "   ${MAGENTA}Python →${RESET} http://localhost:8000"
echo ""

npx concurrently \
  -n "nuxt,python" \
  -c "cyan,magenta" \
  --kill-others-on-fail \
  "nuxt dev" \
  "cd ../python-ai && venv/bin/python -m uvicorn app.main:app --reload --port 8000"
