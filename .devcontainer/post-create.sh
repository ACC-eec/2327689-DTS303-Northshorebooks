#!/usr/bin/env bash
# Codespaces post-create setup for Northshore Books.
# Runs once when the codespace is first built. Marker does not need to run this manually.
set -euo pipefail

echo "==> Ensuring runtime directories exist..."
mkdir -p storage/logs

echo "==> Installing system packages required by mysqlclient..."
sudo apt-get update -q
sudo apt-get install -y -q --no-install-recommends \
  default-libmysqlclient-dev \
  pkg-config \
  build-essential

echo "==> Installing Python requirements..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo "==> Waiting for MySQL to accept connections..."
ATTEMPTS=0
until python -c "import MySQLdb; MySQLdb.connect(host='127.0.0.1', user='root', passwd='northshore_root_pw', db='northshore_books')" 2>/dev/null; do
  ATTEMPTS=$((ATTEMPTS + 1))
  if [ $ATTEMPTS -gt 30 ]; then
    echo "MySQL did not become ready in time. Aborting."
    exit 1
  fi
  sleep 2
done
echo "    MySQL is up."

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Creating default admin user (admin / NorthshoreAdmin1234!)..."
python manage.py shell <<'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'NorthshoreAdmin1234!')
    print('    superuser "admin" created.')
else:
    print('    superuser "admin" already exists.')
PYEOF

echo "==> Seeding sample books from Open Library..."
python manage.py seed_from_openlibrary || echo "    (seeder skipped — non-fatal)"

cat <<'BANNER'

================================================================
  Northshore Books is ready.

  To run the site:
      python manage.py runserver 0.0.0.0:8000

  Then open the forwarded URL on port 8000 (Codespaces will
  prompt you, or check the "Ports" tab).

  Admin URL:   /admin/
  Username:    admin
  Password:    NorthshoreAdmin1234!

  API docs:    /api/docs/
================================================================
BANNER
