# Расширения платформы (Фазы 8+)

После запуска Фаз 0–7 можешь добавлять опциональные модули **без переделки ядра**
(Core остаётся неизменным, новые сервисы просто подключаются через compose-оверлей).

## Установленные расширения

### Фаза 8a: Maigret (мега-OSINT)

**Уже встроено в core** — не требует отдельного развёртывания. `maigret` установлен
в worker-образ, адаптер зарегистрирован в реестре.

```bash
# После развёртывания core-backend:
# Запустить скан maigret → POST /api/scans
#   {"target_id": 1, "tool": "maigret", "kind": "username", "value": "alice"}
```

Maigret проверяет **3000+ сайтов** (vs. sherlock 300), медленнее но полнее.

### Фаза 8b: Stirling-PDF (обработка артефактов)

**50+ инструментов PDF** (объединение, разделение, OCR, подпись, сжатие и т.д.).
Полезна для работы с собранными евидденсом.

```bash
docker compose -f docker-compose.yml -f docker-compose.extra-modules.yml \
  --profile core --profile pdf up -d
# https://pdf.${ROOT_DOMAIN}
```

### Фаза 8c: Open WebUI (альтернатива sub2api)

**Веб-интерфейс к локальным/облачным моделям** (Ollama, OpenAI, Claude и т.д.).
Может заменить или дополнить sub2api.

```bash
docker compose -f docker-compose.yml -f docker-compose.extra-modules.yml \
  --profile core --profile webui up -d
# https://webui.${ROOT_DOMAIN}
# Подключён к sub2api или Ollama (см. compose env)
```

### Фаза 8d: Uptime Kuma (мониторинг инфры)

**Отслеживание доступности** целевых сервисов (HTTP, DNS, TCP, Docker, WebSocket).
Полезна для долгосрочного мониторинга инфры-целей.

```bash
docker compose -f docker-compose.yml -f docker-compose.extra-modules.yml \
  --profile core --profile monitoring up -d
# https://uptime.${ROOT_DOMAIN}
```

## Архитектура расширений

```
Aziral Core (неизменное) ← RestAPI
    ↓ (读)
    ├─ OSINT Module (maigret + старые) → findings-БД
    ├─ Utils (Stirling-PDF) → артефакты
    ├─ AI (open-webui или sub2api)
    └─ Monitoring (uptime-kuma) → статусы целей
```

**Ключ**: каждое расширение:
- Живёт в отдельном profile (`pdf`, `webui`, `monitoring`)
- Подключается за Traefik+SSO (нет отдельного входа)
- Может читать БД findings (для интеграции)
- Может вызывать Core API (через `X-Aziral-Key` если нужно)

## Полная команда запуска (все модули)

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.extra-modules.yml \
  --profile core \
  --profile osint \
  --profile analytics \
  --profile automation \
  --profile terminal \
  --profile pdf \
  --profile webui \
  --profile monitoring \
  up -d --build
```

## Добавить свой модуль

Чтобы добавить **новый инструмент** (не переписывая Core):

1. Создать сервис в `docker-compose.extra-modules.yml` (новый профиль).
2. Если нужна интеграция с Core (читать/писать findings): добавить REST endpoint в Core
   или использовать `X-Aziral-Key` для вызова API.
3. Подключить к `aziral_edge`/`aziral_internal` сетям.
4. Раскинуть Traefik-labels для SSO.

Пример: добавить GitNexus (граф кода для dev-ассистентов) — новый profile `codeintel`,
подключить к edge, запустить как dev-инструмент без интеграции с OSINT.
