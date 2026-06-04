#!/usr/bin/env bash
# Применяет ROOT_DOMAIN из .env во все файлы, где Traefik file-provider
# и Authentik blueprints требуют жёстко зашитый домен (file-provider не
# умеет env-substitute, blueprint context — умеет, но менять YAML быстрее sed'ом).
set -euo pipefail
cd "$(dirname "$0")/.."

ROOT_DOMAIN="$(grep '^ROOT_DOMAIN=' .env | cut -d= -f2)"
if [[ -z "$ROOT_DOMAIN" ]]; then
  echo "[configure-domain] ROOT_DOMAIN не найден в .env" >&2
  exit 1
fi

echo "[configure-domain] применяю домен: $ROOT_DOMAIN"

# Заменяем все жёстко зашитые "aziral.localhost" на $ROOT_DOMAIN.
# (старое значение по умолчанию, заведено в шаблонах).
files=(
  infra/traefik/dynamic/services.yml
  infra/auth/blueprints/aziral-forward-auth.yaml
  infra/auth/blueprints/aziral-brand.yaml
)

for f in "${files[@]}"; do
  if [[ -f "$f" ]]; then
    sed -i.bak "s|aziral\.localhost|${ROOT_DOMAIN}|g" "$f"
    rm -f "${f}.bak"
    echo "  обновлено: $f"
  fi
done

echo "[configure-domain] готово. Перезапусти стек: docker compose ... up -d --force-recreate traefik authentik-server authentik-worker"
