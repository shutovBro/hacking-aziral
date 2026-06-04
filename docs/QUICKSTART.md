# Quickstart Hacking-Aziral (локально)

## 1. Подготовка

```bash
cd hacking-aziral
make secrets                   # сгенерировать .env с секретами
```

## 2. /etc/hosts (один раз)

Браузер должен резолвить поддомены платформы в 127.0.0.1. Запусти **с sudo**:

```bash
sudo ./scripts/setup-hosts.sh
```

Если не доверяешь скрипту — добавь вручную в `/etc/hosts`:

```
127.0.0.1 aziral.aziral.localhost auth.aziral.localhost traefik.aziral.localhost
127.0.0.1 spiderfoot.aziral.localhost superset.aziral.localhost
127.0.0.1 flows.aziral.localhost cron.aziral.localhost term.aziral.localhost
```

## 3. Поднять ядро

```bash
make core         # Traefik + Authentik + Core + БД (≈3 мин при первом запуске)
```

При первом запуске Authentik долго мигрирует БД — это **нормально, до 5 минут**.

## 4. Войти

Открой `https://aziral.aziral.localhost`

Браузер ругнётся на самоподписанный сертификат (это OK для localhost — на проде
поставь домен и Let's Encrypt). Дай согласие.

Откроется форма входа Authentik:
- **user**: `akadmin`
- **password**: из `.env` (`grep AUTHENTIK_BOOTSTRAP_PASSWORD .env`)

После входа → попадёшь в **Aziral Core дашборд**. SSO работает для всех модулей —
открыв любой другой поддомен (superset/spiderfoot/...), снова логиниться не нужно.

## 5. Поднять остальные модули

```bash
# OSINT-движки (spiderfoot) + web-terminal
docker compose --profile osint --profile terminal up -d --build

# Аналитика (Superset)
docker compose --profile analytics up -d
# затем применить VIEW (см. docs/ANALYTICS.md):
docker compose exec -T postgres psql -U aziral -d aziral_core < analytics/superset/views.sql

# Автоматизация (Activepieces + Cronicle)
docker compose --profile automation up -d

# Всё сразу:
make up
```

## 6. Тест работы

После входа в дашборд:
1. **Targets** → создай цель с scope (например `acme.com`)
2. **Run Recon** → выбери `theharvester` → введи `acme.com` → Запуск
3. **Results** → увидишь найденные email/host (через несколько секунд)

Попробуй ввести значение **вне scope** — скан заблокируется, в audit_log появится запись.

## 7. Стоп / перезапуск

```bash
docker compose down            # остановить
docker compose --profile core up -d   # снова поднять
```

## Что дальше

- `docs/RUNBOOK.md` — типовые операции
- `docs/ANALYTICS.md` — настройка Superset
- `docs/AUTOMATION.md` — плейбуки и расписания
- `docs/EXTENSIONS.md` — Stirling-PDF, Open WebUI, Uptime Kuma
- `docs/SECURITY.md` — политика scope и безопасность

## Troubleshooting

| Симптом | Решение |
|---|---|
| Браузер не открывает `*.aziral.localhost` | Запусти `sudo ./scripts/setup-hosts.sh` |
| Authentik unhealthy >5 мин | `docker compose logs authentik-server` — обычно докатывает миграции |
| 404 от Traefik | Проверь `docker compose ps` — нужный сервис должен быть Up |
| Login не пускает | Сверь пароль с `.env` (`AUTHENTIK_BOOTSTRAP_PASSWORD`) |
