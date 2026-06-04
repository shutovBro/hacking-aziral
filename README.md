# Hacking-Aziral 🛡️

Единая self-hosted платформа для **авторизованного** OSINT и пентеста. Собирает разнородные
open-source инструменты под один вход (SSO), единый дашборд и **единую модель данных**.

> ⚠️ **Только для авторизованного использования.** Каждый скан обязан ссылаться на
> запись об авторизованной цели (scope). Запуски вне scope блокируются и пишутся в
> audit-log. Платформа предназначена для тестирования собственной/разрешённой
> инфраструктуры, обучения и CTF.

## Архитектура (control plane)

Hacking-Aziral — это **тонкий слой оркестрации (Aziral Core)**, который связывает
существующие инструменты как сервисы за общим reverse-proxy + SSO. OSINT-инструменты
нормализуют вывод в единую схему `targets → entities → findings`.

```
Браузер ─SSO─▶ Traefik (TLS) ─▶ Authentik (forward-auth)
                                   │
   ┌───────────┬──────────────────┼───────────────┬──────────────┐
 Aziral Core  spiderfoot       Superset (BI)   activepieces    remnawave
 (UI + API)   recon-ng/...                      cronicle        sub2api
   │          (Celery workers)                                  ttyd (clifm,
   ▼                                                            hackingtool)
 Postgres (targets, scope, audit, НОРМАЛИЗОВАННЫЕ findings) ◀── читает Superset
```

## Профили docker-compose

| Профиль | Что поднимает |
|---|---|
| `core` | Traefik, Authentik, Postgres, Redis, Aziral Core (backend+frontend) |
| `osint` | spiderfoot, recon-ng, theHarvester/sherlock/holehe воркеры, hackingtool |
| `automation` | activepieces, cronicle |
| `analytics` | apache/superset |
| `ai` | sub2api, mobileagent |
| `net` | remnawave (Xray прокси-панель) |
| `terminal` | ttyd web-terminal (clifm, hackingtool) |

```bash
# Поднять только ядро
docker compose --profile core up -d

# Поднять ядро + OSINT + аналитику
docker compose --profile core --profile osint --profile analytics up -d

# Всё сразу
docker compose --profile core --profile osint --profile automation \
  --profile analytics --profile ai --profile net --profile terminal up -d
```

## Быстрый старт

```bash
cp .env.example .env        # затем заполнить секреты (см. SECURITY.md)
./scripts/gen-secrets.sh    # сгенерировать случайные секреты в .env
docker compose --profile core up -d
# открыть https://aziral.localhost (или свой домен из .env)
```

## Доступ по поддоменам (из .env: ROOT_DOMAIN)

| URL | Сервис | Профиль |
|---|---|---|
| `https://aziral.${ROOT_DOMAIN}` | Aziral Core (дашборд) | core |
| `https://auth.${ROOT_DOMAIN}` | Authentik (SSO) | core |
| `https://spiderfoot.${ROOT_DOMAIN}` | SpiderFoot | osint |
| `https://superset.${ROOT_DOMAIN}` | Superset BI | analytics |
| `https://flows.${ROOT_DOMAIN}` | Activepieces | automation |
| `https://cron.${ROOT_DOMAIN}` | Cronicle | automation |
| `https://proxy.${ROOT_DOMAIN}` | Remnawave | net |
| `https://term.${ROOT_DOMAIN}` | Web-terminal | terminal |
| `https://pdf.${ROOT_DOMAIN}` | Stirling-PDF | pdf (опц) |
| `https://webui.${ROOT_DOMAIN}` | Open WebUI | webui (опц) |
| `https://uptime.${ROOT_DOMAIN}` | Uptime Kuma | monitoring (опц) |

### OSINT-инструменты (встроены в Core)

- **sherlock**, **holehe**, **theHarvester**, **spiderfoot** — как раньше
- **maigret** — мега-OSINT (3000+ сайтов) — новое в Фазе 8

### Быстрый старт

```bash
make core          # ядро (фазы 0–1)
make up            # основные модули (фазы 2–6)
make up-extra      # + расширения (фаза 8)
```

См. [docs/](docs/) — архитектура, runbook, scope-политика, расширения.
