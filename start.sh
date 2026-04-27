#!/bin/bash
# Northshore Books - one-click launcher for the marker.
# Does everything end-to-end: venv, deps, .env, storage dirs, migrations,
# admin user, sample books, then opens the site in your browser.
set -e

echo "========================================"
echo "Northshore Books - Starting"
echo "========================================"
echo ""

# 0) Python check
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is not installed or not on PATH."
    echo "Install Python 3.11+ and try again."
    exit 1
fi

# 1) Virtual environment
if [ ! -d "venv" ]; then
    echo "[1/7] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[1/7] Virtual environment already exists."
fi

# 2) Activate
echo "[2/7] Activating virtual environment..."
# shellcheck disable=SC1091
source venv/bin/activate

# 3) Dependencies (pip skips anything already installed)
echo "[3/7] Installing dependencies (first run takes a minute)..."
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# 4) .env (defaults to SQLite for local marker run)
if [ ! -f ".env" ]; then
    echo "[4/7] Creating .env from ENV_EXAMPLE.txt (SQLite default)..."
    cp ENV_EXAMPLE.txt .env
else
    echo "[4/7] .env already present."
fi

# 5) Runtime directories
mkdir -p storage/logs
echo "[5/7] Runtime directories ready."

# 6) Migrations
echo "[6/7] Running database migrations..."
python manage.py migrate --noinput

# 7) Admin user + sample books
echo "[7/7] Creating admin user and seeding sample books..."
python manage.py shell --command "from django.contrib.auth import get_user_model; U=get_user_model(); U.objects.filter(username='admin').exists() or U.objects.create_superuser('admin','admin@example.com','NorthshoreAdmin1234!')"
python manage.py seed_from_openlibrary 2>/dev/null || echo "    (seeder skipped - non-fatal, the site still runs)"

cat <<'BANNER'

========================================
  Northshore Books is ready.
  Opening http://127.0.0.1:8000 ...

  Admin URL:   /admin/
  Username:    admin
  Password:    NorthshoreAdmin1234!
  API docs:    /api/docs/

  Press Ctrl+C to stop the server.
========================================

BANNER

# Open browser in background (best-effort across platforms)
( sleep 2 && ( xdg-open http://127.0.0.1:8000/ >/dev/null 2>&1 \
            || open http://127.0.0.1:8000/ >/dev/null 2>&1 \
            || true ) ) &

python manage.py runserver
