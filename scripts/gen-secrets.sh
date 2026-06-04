#!/usr/bin/env bash
# Генерирует случайные секреты и записывает их в .env, заменяя плейсхолдеры __CHANGE_ME__.
# Идемпотентно для уже заполненных значений (трогает только __CHANGE_ME__).
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "[gen-secrets] .env не найден — копирую из .env.example"
  cp .env.example .env
fi

# Миграция: дописать в .env ключи из .env.example, которых там ещё нет.
while IFS= read -r line; do
  [[ "$line" =~ ^[A-Z_][A-Z0-9_]*= ]] || continue
  key="${line%%=*}"
  if ! grep -q "^${key}=" .env; then
    echo "[gen-secrets] добавляю отсутствующий ключ: ${key}"
    printf '%s\n' "$line" >> .env
  fi
done < .env.example

rand() { openssl rand -hex 32; }

# Заменяем каждую строку, где значение == __CHANGE_ME__, на случайный секрет.
tmp="$(mktemp)"
while IFS= read -r line; do
  if [[ "$line" == *"=__CHANGE_ME__" ]]; then
    key="${line%%=*}"
    printf '%s=%s\n' "$key" "$(rand)" >> "$tmp"
  else
    printf '%s\n' "$line" >> "$tmp"
  fi
done < .env
mv "$tmp" .env

# Синхронизируем пароль Postgres внутри CORE_DATABASE_URL и CORE_REDIS_URL.
pg_pass="$(grep '^POSTGRES_PASSWORD=' .env | cut -d= -f2-)"
redis_pass="$(grep '^REDIS_PASSWORD=' .env | cut -d= -f2-)"
# macOS/BSD sed совместимость
sed -i.bak -E "s#(CORE_DATABASE_URL=postgresql\+psycopg://aziral:)[^@]*(@)#\1${pg_pass}\2#" .env
sed -i.bak -E "s#(CORE_REDIS_URL=redis://:)[^@]*(@)#\1${redis_pass}\2#" .env
rm -f .env.bak

echo "[gen-secrets] Готово. Секреты записаны в .env"
echo "[gen-secrets] ВАЖНО: проверь, что .env в .gitignore (он там есть)."
