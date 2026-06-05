# Hacking-Aziral — контекст проекта для Claude

> Этот файл — справочник для будущих сессий. Прочитай ПОЛНОСТЬЮ перед действиями.

## Что это

Единая self-hosted платформа для авторизованной OSINT-разведки и пентеста.
Control plane (наш код Aziral Core) оркестрирует ~15 open-source инструментов
за единым SSO. Все OSINT-результаты нормализуются в единую схему БД.

**Контекст использования**: авторизованный пентест / OSINT по своим целям.
Платформа задумана с встроенным scope-gate (fail-closed) — сканы вне scope
блокируются (`enforce`) или логируются с пометкой WARN (`warn`).

## Где что

| Что | Где |
|---|---|
| Локальный код | `/Users/mpmr/Documents/projects/КИБЕРБЕЗОПАСНОСТЬ/hacking-aziral` |
| Серверный код | `aziral:/home/olzhas/hacking-aziral` (SSH alias `aziral`) |
| План | `/Users/mpmr/.claude/plans/iterative-shimmying-badger.md` |
| Документация | `docs/` (8+ файлов: ARCHITECTURE, RUNBOOK, SECURITY, DEPLOY-SERVER, etc) |
| Тесты backend | `core/backend/tests/` (37 тестов, 88% coverage) |

## Production деплой

**Сервер**: 46.225.166.18 (Debian, 30 GB RAM, Docker 29.3.1)
**SSH**: `ssh aziral` (как пользователь `olzhas`, ключ `~/.ssh/aziral_olzhas`)
**За**: Nginx Proxy Manager (NPM) на 80/443 — наш Traefik НЕ публикует порты наружу
**SSL**: Let's Encrypt через NPM API (автоматически)
**Домен**: `cybersecurity.aziral.com` (Cloudflare DNS, серое облако — DNS only)

### Доступы

- **Главный URL**: https://cybersecurity.aziral.com
- **Логин Authentik / Uptime Kuma**: `olzhikbro` / `karolbmira2004`
- **Sudo на сервере (`olzhas`)**: `Skyler2004!`
- **Telegram бот для алертов**: `@aziral_security_bot`, chat_id `8144239088`,
  токен в `/etc/ssh/ssh-notify.sh.bak` или Vaultwarden
- **Vaultwarden** (хранилище секретов): https://vault.aziral.com
- Все секреты сервиса: `~/hacking-aziral/.env` на сервере (НЕ в git)

### Все URLs (все за SSO)

```
https://cybersecurity.aziral.com           — Aziral Core (главный)
https://auth.cybersecurity.aziral.com      — Authentik SSO
https://spiderfoot.cybersecurity.aziral.com
https://superset.cybersecurity.aziral.com  — BI/дашборды
https://flows.cybersecurity.aziral.com     — Activepieces
https://cron.cybersecurity.aziral.com      — Cronicle
https://term.cybersecurity.aziral.com      — web-terminal (ttyd)
```

### Команды на сервере

```bash
# Запуск платформы
cd ~/hacking-aziral
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile core up -d
# + другие профили: osint analytics automation terminal ai net

# Логи
docker logs aziral-<service>-1

# Перезапуск frontend (после правок)
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --profile core up -d --build core-frontend
```

## Архитектура (кратко)

```
Internet → NPM:443 (TLS, LE certs) → aziral-traefik-1:80 (HTTP, file-provider)
                                            ↓ forward-auth → Authentik
                                            ↓
                              core-frontend / core-backend / spiderfoot / ...
                                            ↓
                              postgres (single cluster, multi-db) + redis
```

**Ключевые решения**:
- Traefik: **file-provider** (не docker discovery) — Docker 29.4 API 1.54 несовместим с Traefik 3.3
- Trust forwarded headers от NPM: `forwardedHeaders.insecure: true` в `traefik-prod.yml`
- Authentik: blueprints в `infra/auth/blueprints/` автоматизируют Application/Provider/Brand/Outpost
- Embedded outpost: `_config` JSON в БД задаёт публичные URL (через blueprint)

## Когда что-то ломается

| Проблема | Решение |
|---|---|
| OAuth redirect_uri = `http://...` вместо https | `forwardedHeaders.insecure: true` в traefik-prod.yml |
| 404 от Traefik на legit домен | Проверь `infra/traefik/dynamic/services.yml` — хосты должны совпадать с ROOT_DOMAIN |
| 308 redirect loop | TLS-terminator у NPM → в traefik-prod.yml НЕ должен быть `web.http.redirections` |
| Authentik unhealthy >5 мин | Просто ждёт миграций — посмотри логи: `docker logs aziral-authentik-server-1` |
| Blueprint `error` | `docker exec aziral-authentik-worker-1 ak shell -c "..."` для отладки validate() |
| `cybersecurity.aziral.com` не резолвит | Cloudflare DNS — серое облако (DNS only), не оранжевое (proxy) |
| Activepieces restart loop | `AP_ENCRYPTION_KEY` должен быть **32 hex chars** (16 bytes) |

## Структура кода

```
hacking-aziral/
├── core/
│   ├── backend/                # FastAPI (Python)
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── models.py       # targets → entities → findings + jobs + audit
│   │   │   ├── scope/gate.py   # scope-gate (fail-closed логика)
│   │   │   ├── auth.py         # SSO headers + X-Aziral-Key для сервисов
│   │   │   ├── orchestrators/  # адаптеры инструментов (1 файл = 1 инструмент)
│   │   │   ├── routers/        # FastAPI endpoints
│   │   │   └── workers/        # Celery tasks
│   │   ├── tests/              # 37 тестов, 88% покрытие
│   │   └── Dockerfile / Dockerfile.worker (с OSINT CLI)
│   └── frontend/               # React + Vite + TS (без CSS-фреймворков, токены в global.css)
├── infra/
│   ├── traefik/
│   │   ├── traefik.yml         # dev (с ACME staging)
│   │   ├── traefik-prod.yml    # prod (без HTTP→HTTPS redirect, trust forwarded)
│   │   └── dynamic/            # services.yml + middlewares.yml (file provider)
│   └── auth/blueprints/        # Authentik blueprints (forward-auth, brand)
├── tools/                      # Dockerfile'ы для spiderfoot, webterm
├── analytics/superset/         # config + register_db.py + views.sql + bootstrap.sh
├── docker-compose.yml          # core + osint + analytics + automation + terminal
├── docker-compose.prod.yml     # production overlay (без портов наружу)
├── docker-compose.extra-modules.yml  # Stirling-PDF + Open WebUI + Uptime Kuma
└── scripts/                    # gen-secrets, configure-domain, init-vendor, setup-hosts
```

## Как добавить новый OSINT-инструмент

1. `core/backend/app/orchestrators/<tool>.py` — функция `run(kind, value) -> list[NormalizedFinding]`
2. Регистрация в `orchestrators/__init__.py` (`TOOL_REGISTRY`)
3. Установка в `Dockerfile.worker` (RUN pip install / git clone)
4. Тест в `tests/test_orchestrators.py`
5. Кнопка в UI: `frontend/src/pages/RunRecon.tsx` (добавить в `TOOL_KINDS`)
6. Rebuild + redeploy

## Как добавить новый сервис (модуль)

1. Сервис в `docker-compose.yml` (с profile) или `docker-compose.extra-modules.yml`
2. Route в `infra/traefik/dynamic/services.yml`
3. Subdomain в Cloudflare (или wildcard `*.cybersecurity.aziral.com` уже есть)
4. Proxy host в NPM через API (см. `docs/DEPLOY-SERVER.md`)
5. LE certificate через NPM API
6. Карточка в `frontend/src/pages/Modules.tsx` (+ префикс в `KNOWN_PREFIXES`)

## Git

- 3 коммита в `main`, никуда не запушено (готово для `gh repo create` или ручного remote)
- 4 коммит в работе — нужно закоммитить фикс Modules.tsx + переключение в warn mode

## Security hardening (2026-06-06)

### Что закрыто на сервере

- **UFW** активен. Allow: 22 SSH, 80/443 HTTP(S), Mailcow-порты (25/110/143/465/587/993/995/4190), GitLab 7777, TURN/STUN 3478, 3010-3030 misc. Прочее deny.
- **NPM admin :81** доступен **только с моего IP `95.59.96.151`** (iptables INPUT rule, persisted через `iptables-persistent`). Проверено: US/DE/FI = connection timed out.
- **SSH**: `PermitRootLogin no`, `PasswordAuthentication no`, `MaxAuthTries 3`, `LoginGraceTime 30`. Только key-based.
- **fail2ban**: SSH jail активен (ban 24h после 3 попыток).
- **unattended-upgrades**: Debian security патчи автоматом.
- **Watchtower**: контейнерные обновления опт-ин через label `com.centurylinklabs.watchtower.enable=true`, по воскресеньям 04:00 Almaty. Контейнер `aziral-watchtower`.
- **Backup**: `/usr/local/sbin/aziral-backup.sh` через cron daily 03:30 → `/var/backups/aziral/` (pg_dumpall + 6 томов). Retention 14 дней.

### Authentik security blueprint

`infra/auth/blueprints/aziral-security-policy.yaml`:
- Password policy `aziral-strong-password` — мин 12 chars, обязательны upper/lower/digit/symbol.
- TOTP stages созданы (`aziral-totp-setup`, `aziral-totp-validate` с `not_configured_action=skip`).
- **Дальше руками в UI**: чтобы реально включить policy — Customisation → Policies → Bindings → привязать к prompt-stage / user creation flow. Для 2FA на свой аккаунт: User menu → MFA → Add TOTP.

### Cloudflare (отложено)

Включали proxy для `cybersecurity.*` → откатили: бесплатный CF Universal SSL покрывает только `aziral.com` + `*.aziral.com` (один уровень), наш домен второго уровня требует $10/мес Advanced Certificate Manager.

Альтернатива на будущее: купить плоский домен (`hackaziral.com`, etc.), мигрировать туда — Universal SSL покроет всё бесплатно, IP скроется.

### Что НЕ закрыто (compromise)

- Origin IP `46.225.166.18` виден через DNS (cybersecurity.*, mail.aziral.com, gitlab.aziral.com и т.п.). Прямой DDoS возможен, но защищён SSO + rate-limit + fail2ban.
- Mailcow и другие чужие сервисы на том же сервере — открыты как требуется их функционалу.

## Claude Code skills для платформы

В `.claude/skills/anthropic-cybersec/` лежат **754 готовых
cybersecurity/OSINT-скилла** (формат agentskills.io, лицензия Apache-2.0,
маппинг на MITRE ATT&CK + NIST CSF 2.0 + MITRE ATLAS + D3FEND + NIST AI RMF).

- Источник: https://github.com/mukul975/Anthropic-Cybersecurity-Skills
- Установка / обновление: `./scripts/init-skills.sh`
- Не в git (в .gitignore — 44МБ)
- Подхватываются Claude Code автоматически при старте сессии в этой папке

Категории (доминирующие): performing (172), implementing (167),
detecting (87), analyzing (76), hunting (34), exploiting (32),
testing (22). Триггерятся по триггеру задачи (например при разговоре
про DNS exfiltration — поднимется `analyzing-dns-logs-for-exfiltration`).

## Что НЕ реализовано

- **Remnawave Node** — backend+frontend подняты, но Node-узел с Xray нужен на ОТДЕЛЬНОМ VPS (другой IP), иначе egress proxy не даёт другой IP. Hetzner CX22 ~€5/мес. После — в админке создать Inbound + User.
- **MobileAgent / fingerprint-suite** — клонированы в `tools/vendor/`, интеграция руками
- **TOTP enroll** для admin — стейджи в Authentik blueprint готовы, надо зайти в UI и привязать к своему аккаунту
- **Password policy binding** в Authentik — policy создана (`aziral-strong-password`), привязать руками к prompt-stage через Customisation → Policies → Bindings
- **Vaultwarden migration** — креды (sudo, bot token, chat_id) сейчас в CLAUDE.md, надо перенести в Vault
- **CF IP hiding** — отложено. Бесплатный Universal SSL не покрывает 2-level subdomain `cybersecurity.aziral.com`. Решение: $10/мес ACM или плоский домен типа `hackaziral.com`
- **Test restore из backup** — критично сделать однажды для уверенности что бэкапы рабочие
- **Activepieces playbooks** — есть простой alert hook в core-backend; полноценные flow для multi-step orchestration не настроены

## История фаз (что было сделано)

0. Фундамент (Docker, Traefik, SSO, БД)
1. Aziral Core MVP (FastAPI + React)
2. OSINT быстрые CLI (sherlock/holehe/theHarvester)
3. Тяжёлый OSINT (spiderfoot/recon-ng/hackingtool через webterm)
4. Аналитика (Superset + 6 VIEW + auto register DB)
5. Автоматизация (activepieces + Cronicle + service API key)
6. AI + Прокси + Утилиты (документация + compose templates)
7. Полировка + hardening + 37 тестов 88% coverage + e2e Playwright скелет
8. Расширения (maigret + Stirling-PDF + Open WebUI + Uptime Kuma)
9. Live SSO (Authentik blueprints, embedded outpost config)
10. Поднять модули (план)
11. DNS + NPM proxy (Cloudflare, серое облако, wildcard)
12. Полный деплой на сервер (за NPM, файл-провайдер Traefik, LE через NPM API)
13. Live SSO для extra-modules (Stirling-PDF, Open WebUI, Uptime Kuma) + Telegram алерты Kuma
14. AI gateway (sub2api) + Xray panel (Remnawave backend/frontend) подняты за SSO
15. Cronicle 3 weekly OSINT-сканов; алерты `findings.confidence ≥ 0.85` → @aziral_security_bot
16. Superset OSINT Overview dashboard на 6 VIEW + 36 seed-findings; smoke e2e 13/13 OK
17. 754 Anthropic-Cybersecurity-Skills в `.claude/skills/anthropic-cybersec/`
18. Security hardening — UFW, iptables (NPM admin :81), SSH hardening, fail2ban, unattended-upgrades, Watchtower, Authentik password policy + TOTP stages, daily backup → `/var/backups/aziral`

## Ключевые баги исправленные

- `psycopg-binary==3.2.3` устарел → перевели на `3.2.13`
- Traefik 3.3 + Docker 29.4 API 1.54 несовместимы → file-provider
- SpiderFoot v4.0 PyYAML/Cython конфликт → master branch + свежий setuptools
- Superset 4.1 без psycopg2 → bootstrap ставит при старте
- Activepieces require 32 hex AP_ENCRYPTION_KEY → 16 bytes (32 chars)
- OAuth redirect http vs https → forwardedHeaders.insecure: true в Traefik
- NPM /api/nginx/certificates schema — letsencrypt_email/agree убраны в новой версии
- Modules.tsx `slice(-2)` некорректно для 3+ уровневых доменов → KNOWN_PREFIXES логика

## Чего избегать

- НЕ копировать секреты из `Obsidian/Заметки/Сервер AZIRAL...` — там утечки токенов, юзер обновит
- НЕ запускать docker desktop на маке параллельно — он падает под нагрузкой, всё делать на сервере
- НЕ открывать порты 80/443 у нашего Traefik — конфликт с NPM
- НЕ оставлять `SCOPE_MODE=enforce` если юзер просил `warn` (сейчас в warn)
- НЕ модифицировать чужие проекты на сервере (aziral-crm, mailcow, fenix-*, ustazon-*)

## Полезные одно-строчники

```bash
# Все наши контейнеры
ssh aziral 'docker ps --filter "name=aziral-" --format "table {{.Names}}\t{{.Status}}"'

# Логи Authentik
ssh aziral 'docker logs --tail 30 aziral-authentik-server-1 2>&1 | tail -20'

# Применить blueprint вручную
ssh aziral 'docker exec aziral-authentik-worker-1 ak shell -c \
  "from authentik.blueprints.v1.tasks import blueprints_discovery; blueprints_discovery.delay()"'

# Получить NPM API token (для proxy host / cert операций)
ssh aziral 'curl -s -X POST http://localhost:81/api/tokens \
  -H "Content-Type: application/json" \
  -d "{\"identity\":\"aziralgroup@outlook.com\",\"secret\":\"aziral2026\"}"'

# Audit log scope-gate
ssh aziral 'docker exec -e PGPASSWORD=$(grep POSTGRES_PASSWORD ~/hacking-aziral/.env|cut -d= -f2) \
  aziral-postgres-1 psql -U aziral -d aziral_core \
  -c "SELECT actor, action, allowed, detail->>\"value\" AS target, created_at \
      FROM audit_log ORDER BY id DESC LIMIT 10;"'
```
