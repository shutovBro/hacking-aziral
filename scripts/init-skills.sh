#!/usr/bin/env bash
# Клонирует 754 OSINT/cybersecurity-скилла Claude Code в .claude/skills/.
# После клонирования при следующем запуске Claude Code в этой папке
# скиллы станут доступны через Skill tool.
#
# Источник: https://github.com/mukul975/Anthropic-Cybersecurity-Skills
# Лицензия: Apache-2.0
# Маппинги: MITRE ATT&CK, NIST CSF 2.0, MITRE ATLAS, D3FEND, NIST AI RMF
set -euo pipefail
cd "$(dirname "$0")/.."

DEST=".claude/skills/anthropic-cybersec"
mkdir -p "$(dirname "$DEST")"

if [[ -d "$DEST/.git" ]]; then
  echo "[skills] $DEST уже есть — pull"
  git -C "$DEST" pull --ff-only || true
else
  echo "[skills] клонирую Anthropic-Cybersecurity-Skills (754 скилла, ~44МБ)"
  git clone --depth 1 https://github.com/mukul975/Anthropic-Cybersecurity-Skills.git "$DEST"
fi

count=$(ls "$DEST/skills" 2>/dev/null | wc -l | tr -d ' ')
echo "[skills] готово. Скиллов установлено: $count"
echo "[skills] перезапусти Claude Code сессию в этой папке чтобы skill index подхватился"
