# Архитектура Hacking-Aziral

## Слои

```
┌─────────────────────────────────────────────────────────────┐
│ EDGE: Traefik (TLS, поддомены, security-headers, rate-limit) │
│       Authentik forward-auth — единый SSO на ВСЕ сервисы     │
└───────────────┬─────────────────────────────────────────────┘
                │
   ┌────────────┴───────────────────────────────────────────┐
   │ AZIRAL CORE (наш код)                                   │
   │  ├─ FastAPI API (/api): targets, scans, findings        │
   │  ├─ Scope-gate (fail-closed) + audit_log                │
   │  ├─ Celery worker → оркестрация OSINT-инструментов      │
   │  └─ React SPA (дашборд, RunRecon, ResultsExplorer)      │
   └──────┬───────────────────────────┬──────────────────────┘
          │                           │
  ┌───────┴────────┐         ┌────────┴─────────────┐
  │ OSINT движки   │         │ Поддерживающие сервисы│
  │ sherlock holehe│         │ Postgres / Redis      │
  │ theHarvester   │         │ Superset (BI)         │
  │ spiderfoot     │         │ activepieces/cronicle │
  │ webterm(ttyd)  │         │ sub2api / remnawave   │
  └───────┬────────┘         └───────────────────────┘
          │ нормализация
          ▼
  Postgres: targets → entities → findings (+ jobs, audit_log)
                                   ▲
                                   └── читает Superset
```

## Сети
- `aziral_edge` — публикуется через Traefik (только сервисы с UI).
- `aziral_internal` — Postgres, Redis, воркеры, межсервисные вызовы. Портов наружу нет.

## Единая модель данных (`core/backend/app/models.py`)
- `Target` — авторизованная цель + `scope` (JSON).
- `Entity` — нормализованная сущность (`email/username/domain/host/ip/...`), уникальна по `(target,kind,value)`.
- `Finding` — наблюдение из инструмента (`source_tool`, `raw_json`, `confidence`).
- `Job` — запуск скана (статус, params, результат scope-gate).
- `AuditLog` — actor/action/target/allowed/время.

## Поток скана
1. `POST /api/scans` → `scans.launch_scan` ([routers/scans.py](../core/backend/app/routers/scans.py)).
2. **Scope-gate** ([scope/gate.py](../core/backend/app/scope/gate.py)): вне scope → 403 + audit (enforce).
3. В scope → `Job(pending)` + Celery `run_scan` ([workers/tasks.py](../core/backend/app/workers/tasks.py)).
4. Воркер вызывает адаптер ([orchestrators/](../core/backend/app/orchestrators/)), нормализует → `entities`+`findings`.
5. UI Results Explorer и Superset читают единую схему.

## Точки расширения
- Новый инструмент = новый модуль-адаптер в `orchestrators/` + регистрация в `TOOL_REGISTRY`.
- Новый сервис = блок в `docker-compose.yml` с Traefik-labels + `authentik@file`.
- Автоматизация вызывает Core по `internal` с `X-Aziral-Key`.
