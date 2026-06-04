# Runbook Hacking-Aziral

## Первый запуск (локально)

```bash
cd hacking-aziral
make secrets                      # сгенерировать .env
# для локали в .env: ROOT_DOMAIN=aziral.localhost, ACME_CA=staging
make core                         # Traefik + SSO + БД + Core
```
Открыть `https://aziral.localhost` (самоподписанный серт — принять предупреждение).
Первый вход: настроить администратора в Authentik (`https://auth.aziral.localhost`).

## Прод (VPS)

1. DNS: `*.ВАШ_ДОМЕН` → IP сервера.
2. В `.env`: `ROOT_DOMAIN=ВАШ_ДОМЕН`, `ACME_EMAIL=...`, `ACME_CA=production`,
   `CORE_DEV_MODE=false` (уже выставлен для core-backend в compose).
3. `make core` → затем нужные профили:
   ```bash
   docker compose --profile core --profile osint --profile analytics \
     --profile automation --profile terminal up -d --build
   ```
4. Аналитика: применить VIEW (см. [ANALYTICS.md](ANALYTICS.md)).
5. AI/прокси: `./scripts/init-vendor.sh` + оверлей (см. [MODULES.md](MODULES.md)).

## Проверка работоспособности (smoke)

```bash
# API жив
curl -s http://localhost:8000/api/health         # при локальном backend
# тесты backend
cd core/backend && . .venv/bin/activate && pytest        # 35 passed, ~88% cov
# сборка фронтенда
cd core/frontend && npm run build
# валидация compose
docker compose --profile core config -q
```

E2E (нужен поднятый стек):
```bash
cd core/frontend && npm i && npx playwright install && \
  BASE_URL=https://aziral.localhost npm run e2e
```

## Типовые операции

| Задача | Действие |
|---|---|
| Добавить инструмент | новый адаптер в `orchestrators/` + `TOOL_REGISTRY` |
| Сменить режим scope | `.env`: `SCOPE_MODE=enforce|warn` → `up -d` |
| Логи сервиса | `docker compose logs -f <service>` |
| Бэкап БД | `docker compose exec postgres pg_dumpall -U $POSTGRES_USER > dump.sql` |
| Ротация секретов | обновить `.env` → пересоздать сервисы |

## Аварийные ситуации

- **502 за Traefik** — проверь `docker compose ps` и healthcheck postgres/redis.
- **403 на скане** — цель вне scope (ожидаемо) или scope пуст (fail-closed).
- **Celery не берёт задачи** — проверь Redis (`REDIS_PASSWORD`) и `core-worker` логи.
- **Authentik не пускает** — настрой Application+Provider+Outpost (forward-auth) в Authentik.
