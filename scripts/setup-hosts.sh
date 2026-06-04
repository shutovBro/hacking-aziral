#!/usr/bin/env bash
# Добавляет записи в /etc/hosts для локального wildcard-домена Hacking-Aziral.
# Требует sudo. Идемпотентно: если запись уже есть — ничего не меняет.
set -euo pipefail

cd "$(dirname "$0")/.."

ROOT_DOMAIN="$(grep '^ROOT_DOMAIN=' .env | cut -d= -f2)"
if [[ -z "$ROOT_DOMAIN" ]]; then
  echo "[hosts] не нашёл ROOT_DOMAIN в .env" >&2
  exit 1
fi

SUBDOMAINS=(
  ""           # сам ROOT_DOMAIN (хотя обычно не используется)
  "aziral"
  "auth"
  "traefik"
  "spiderfoot"
  "superset"
  "flows"
  "cron"
  "proxy"
  "term"
  "ai"
  "pdf"
  "webui"
  "uptime"
)

MARKER="# hacking-aziral"
TMPFILE="$(mktemp)"

# Убираем старые записи с маркером, добавляем свежие.
sudo grep -v "$MARKER" /etc/hosts > "$TMPFILE" || true
{
  for sub in "${SUBDOMAINS[@]}"; do
    if [[ -n "$sub" ]]; then
      printf "127.0.0.1\t%s.%s\t%s\n" "$sub" "$ROOT_DOMAIN" "$MARKER"
    else
      printf "127.0.0.1\t%s\t%s\n" "$ROOT_DOMAIN" "$MARKER"
    fi
  done
} >> "$TMPFILE"

sudo cp "$TMPFILE" /etc/hosts
rm -f "$TMPFILE"

echo "[hosts] записи добавлены для *.${ROOT_DOMAIN}"
grep "$MARKER" /etc/hosts
