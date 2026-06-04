-- Аналитические VIEW поверх схемы находок (применять к БД aziral_core).
-- Подключите их как «датасеты» в Superset для готовых дашбордов.
-- Применение:  psql "$CORE_DATABASE_URL" -f analytics/superset/views.sql

-- Находки с контекстом цели и сущности (главный датасет).
CREATE OR REPLACE VIEW v_findings_enriched AS
SELECT
    f.id            AS finding_id,
    f.source_tool   AS tool,
    f.confidence    AS confidence,
    f.discovered_at AS discovered_at,
    e.kind          AS entity_kind,
    e.value         AS entity_value,
    t.id            AS target_id,
    t.name          AS target_name
FROM findings f
JOIN entities e ON e.id = f.entity_id
JOIN targets  t ON t.id = e.target_id;

-- Кол-во сущностей по типам в разрезе цели (для bar/pie).
CREATE OR REPLACE VIEW v_entities_by_kind AS
SELECT t.id AS target_id, t.name AS target_name, e.kind AS entity_kind, COUNT(*) AS cnt
FROM entities e
JOIN targets t ON t.id = e.target_id
GROUP BY t.id, t.name, e.kind;

-- Соц-след (sherlock / holehe).
CREATE OR REPLACE VIEW v_social_footprint AS
SELECT t.name AS target_name, e.value AS account, f.source_tool AS tool, f.discovered_at
FROM findings f
JOIN entities e ON e.id = f.entity_id
JOIN targets  t ON t.id = e.target_id
WHERE e.kind = 'social_account';

-- Утечки/компрометации (breach).
CREATE OR REPLACE VIEW v_breaches AS
SELECT t.name AS target_name, e.value AS item, f.raw_json, f.discovered_at
FROM findings f
JOIN entities e ON e.id = f.entity_id
JOIN targets  t ON t.id = e.target_id
WHERE e.kind = 'breach';

-- Карта инфраструктуры: домены/хосты/ip (theHarvester / spiderfoot).
CREATE OR REPLACE VIEW v_infrastructure AS
SELECT t.name AS target_name, e.kind AS entity_kind, e.value AS entity_value, f.source_tool AS tool
FROM findings f
JOIN entities e ON e.id = f.entity_id
JOIN targets  t ON t.id = e.target_id
WHERE e.kind IN ('domain', 'host', 'ip');

-- Активность сканов по статусам (для мониторинга и аудита).
CREATE OR REPLACE VIEW v_jobs_activity AS
SELECT tool, status, COUNT(*) AS cnt, MAX(created_at) AS last_run
FROM jobs
GROUP BY tool, status;
