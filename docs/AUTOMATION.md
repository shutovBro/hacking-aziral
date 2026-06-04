# Автоматизация (Activepieces + Cronicle)

Оба сервиса находятся во внутренней сети и вызывают Aziral Core напрямую
`http://core-backend:8000/api/...`, минуя SSO, но с сервисным ключом
`X-Aziral-Key: $CORE_INTERNAL_API_KEY`.

> Сервисный ключ работает только внутри `aziral_internal`. Снаружи Core
> по-прежнему защищён Authentik SSO.

## Activepieces (no-code плейбуки) — `https://flows.${ROOT_DOMAIN}`

Пример плейбука «новая цель → авто-разведка → уведомление»:

1. **Trigger**: Webhook (или Schedule).
2. **HTTP**: `POST http://core-backend:8000/api/scans`
   - Headers: `X-Aziral-Key: {{secrets.AZIRAL_KEY}}`, `Content-Type: application/json`
   - Body:
     ```json
     { "target_id": 1, "tool": "theharvester", "kind": "domain", "value": "acme.com" }
     ```
3. **HTTP (poll)**: `GET http://core-backend:8000/api/scans/{{step1.id}}` до `status=completed`.
4. **HTTP**: `GET http://core-backend:8000/api/targets/1/findings`.
5. **Notify**: Slack/Telegram/Email с краткой сводкой.

## Cronicle (расписания) — `https://cron.${ROOT_DOMAIN}`

Регулярная переразведка по расписанию. Тип события — **Shell Script**:

```bash
#!/bin/bash
curl -s -X POST http://core-backend:8000/api/scans \
  -H "X-Aziral-Key: ${AZIRAL_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"target_id":1,"tool":"spiderfoot","kind":"domain","value":"acme.com"}'
```

Расписание: например, еженедельно. Cronicle сохранит историю запусков и логи.

## Запуск профиля

```bash
docker compose --profile core --profile automation up -d
```

Первый вход в Cronicle: логин `admin` / `admin` (смените сразу). Activepieces
создаёт администратора при первом открытии UI.
