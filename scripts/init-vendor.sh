#!/usr/bin/env bash
# Клонирует внешние репозитории-зависимости в tools/vendor/ (для сборки образов,
# которые строятся из исходников: sub2api, remnawave, MobileAgent и т.п.).
# Версии можно закрепить, заменив branch/таг.
set -euo pipefail
cd "$(dirname "$0")/.."

VENDOR=tools/vendor
mkdir -p "$VENDOR"

clone() {
  local url="$1" dir="$2"
  if [[ -d "$VENDOR/$dir/.git" ]]; then
    echo "[vendor] $dir уже есть — pull"
    git -C "$VENDOR/$dir" pull --ff-only || true
  else
    echo "[vendor] клонирую $dir"
    git clone --depth 1 "$url" "$VENDOR/$dir"
  fi
}

clone https://github.com/Wei-Shaw/sub2api.git            sub2api
clone https://github.com/remnawave/panel.git             remnawave
clone https://github.com/X-PLUG/MobileAgent.git          mobileagent
clone https://github.com/apify/fingerprint-suite.git     fingerprint-suite

echo "[vendor] готово. Теперь: docker compose --profile ai --profile net build"
