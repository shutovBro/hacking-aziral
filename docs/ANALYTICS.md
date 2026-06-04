# Аналитика (Superset)

Superset подключён к БД находок `aziral_core` как источник «Aziral Findings»
(регистрируется автоматически при старте через `register_db.py`).

## Шаги настройки

1. Поднять профиль: `docker compose --profile core --profile analytics up -d`
2. Применить аналитические VIEW к БД находок:
   ```bash
   docker compose exec -T postgres psql -U "$POSTGRES_USER" -d aziral_core \
     < analytics/superset/views.sql
   ```
3. Открыть `https://superset.${ROOT_DOMAIN}` (вход — admin из `.env`).
4. В Superset: Data → Datasets → + Dataset → база «Aziral Findings» → выбрать VIEW.

## Рекомендуемые дашборды

| Дашборд | Датасет | Тип графиков |
|---|---|---|
| Обзор по цели | `v_entities_by_kind` | Big Number, Pie по `entity_kind` |
| Соц-след | `v_social_footprint` | Table, Bar по `tool` |
| Утечки email | `v_breaches` | Table, Time-series по `discovered_at` |
| Карта инфраструктуры | `v_infrastructure` | Table, Bar по `entity_kind` |
| Активность сканов | `v_jobs_activity` | Bar по `status`, Big Number |

## Экспорт/импорт дашбордов

После ручной сборки выгрузите дашборды в репозиторий для воспроизводимости:
```bash
docker compose exec superset superset export-dashboards -f /tmp/dash.zip
docker compose cp superset:/tmp/dash.zip analytics/superset/dashboards.zip
```
Импорт на новой инсталляции: `superset import-dashboards -p /path/dash.zip`.
