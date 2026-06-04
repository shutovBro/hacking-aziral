#!/usr/bin/env bash
# Инициализация Superset: миграции, админ, init, регистрация БД находок, запуск.
set -e

# Superset 4.1 не включает драйвер Postgres — ставим (идемпотентно).
echo "[superset] устанавливаю psycopg2-binary (драйвер Postgres)"
pip install --quiet --no-cache-dir 'psycopg2-binary<3' || true

echo "[superset] db upgrade"
superset db upgrade

echo "[superset] create admin (идемпотентно)"
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USER:-admin}" \
  --firstname Aziral --lastname Admin \
  --email "${SUPERSET_ADMIN_EMAIL:-admin@aziral.local}" \
  --password "${SUPERSET_ADMIN_PASSWORD:-admin}" || true

echo "[superset] init roles/perms"
superset init

echo "[superset] регистрирую БД находок"
python /app/pythonpath/register_db.py || echo "[superset] WARN: не удалось зарегистрировать БД (добавьте вручную в UI)"

echo "[superset] запуск сервера"
exec /usr/bin/run-server.sh
