#!/bin/bash
# Создаёт отдельные БД для сервисов платформы внутри одного кластера Postgres.
# Запускается контейнером postgres при первой инициализации (docker-entrypoint-initdb.d).
set -euo pipefail

create_db() {
  local db="$1"
  echo "[postgres-init] создаю БД $db (если не существует)"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-SQL
    SELECT 'CREATE DATABASE $db'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
SQL
}

# Все логические БД платформы принадлежат основному пользователю POSTGRES_USER.
for db in aziral_core authentik superset activepieces sub2api remnawave; do
  create_db "$db"
done

echo "[postgres-init] готово"
