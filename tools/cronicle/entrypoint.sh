#!/usr/bin/env bash
# Запуск Cronicle: первичная настройка хранилища (если пусто), затем foreground.
set -e

DATA_DIR=/opt/cronicle/data

# Первый запуск: инициализируем storage и админ-данные.
if [ ! -d "${DATA_DIR}/global" ]; then
  echo "[cronicle] первичная настройка storage"
  /opt/cronicle/bin/control.sh setup
fi

echo "[cronicle] старт (foreground)"
exec node /opt/cronicle/lib/main.js --foreground --echo
