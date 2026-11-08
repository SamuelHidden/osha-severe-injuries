-- ============================================================================
-- 00_load.sql — загрузка данных из Data/processed/DataBaseFiles в OSHA_db
--
-- Выполнять через psql ИЗ КОРНЯ ПРОЕКТА (пути к CSV относительные),
-- после 00_schema.sql:
--
--   psql -d OSHA_db -f SQL/00_load.sql
--
-- \copy читает файлы на стороне клиента, поэтому права суперпользователя
-- не нужны. Сначала справочники, потом факт-таблица — иначе не пройдут FK.
-- Пустое поле в CSV загружается как NULL.
-- ============================================================================

\set ON_ERROR_STOP on

BEGIN;

\copy body_part_lookup FROM 'Data/processed/DataBaseFiles/body_part_lookup.csv' WITH (FORMAT csv, HEADER true)
\copy event_lookup     FROM 'Data/processed/DataBaseFiles/event_lookup.csv'     WITH (FORMAT csv, HEADER true)
\copy nature_lookup    FROM 'Data/processed/DataBaseFiles/nature_lookup.csv'    WITH (FORMAT csv, HEADER true)
\copy source_lookup    FROM 'Data/processed/DataBaseFiles/source_lookup.csv'    WITH (FORMAT csv, HEADER true)
\copy naics_lookup     FROM 'Data/processed/DataBaseFiles/naics_lookup.csv'     WITH (FORMAT csv, HEADER true)
\copy injuries         FROM 'Data/processed/DataBaseFiles/injuries.csv'         WITH (FORMAT csv, HEADER true)

COMMIT;

ANALYZE;

-- Проверка: ожидается 205 / 476 / 251 / 1643 / 2442 / 105 996 строк
SELECT 'body_part_lookup' AS table_name, COUNT(*) AS rows FROM body_part_lookup
UNION ALL SELECT 'event_lookup',  COUNT(*) FROM event_lookup
UNION ALL SELECT 'nature_lookup', COUNT(*) FROM nature_lookup
UNION ALL SELECT 'source_lookup', COUNT(*) FROM source_lookup
UNION ALL SELECT 'naics_lookup',  COUNT(*) FROM naics_lookup
UNION ALL SELECT 'injuries',      COUNT(*) FROM injuries;
