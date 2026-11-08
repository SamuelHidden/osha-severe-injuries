-- ============================================================================
-- 00_schema.sql — структура базы OSHA_db (PostgreSQL 14+)
--
-- Звезда из одной факт-таблицы (injuries) и пяти справочников.
-- Выполнять в ПУСТОЙ базе, затем загрузить данные скриптом 00_load.sql:
--
--   createdb OSHA_db
--   psql -d OSHA_db -f SQL/00_schema.sql
--   psql -d OSHA_db -f SQL/00_load.sql      -- из корня проекта
-- ============================================================================


-- ---------------------------------------------------------------------------
-- Справочники OIICS (коды иерархические: первая цифра = раздел)
-- ---------------------------------------------------------------------------

CREATE TABLE body_part_lookup (
    code  integer PRIMARY KEY,
    title varchar NOT NULL
);
COMMENT ON TABLE body_part_lookup IS 'Справочник частей тела (Part of Body / Part of Body Title)';

CREATE TABLE event_lookup (
    code  integer PRIMARY KEY,
    title varchar NOT NULL
);
COMMENT ON TABLE event_lookup IS 'Справочник типов событий (Event / EventTitle)';

CREATE TABLE nature_lookup (
    code  integer PRIMARY KEY,
    title varchar NOT NULL
);
COMMENT ON TABLE nature_lookup IS 'Справочник типов травмы (Nature / NatureTitle)';

CREATE TABLE source_lookup (
    code  integer PRIMARY KEY,
    title varchar NOT NULL
);
COMMENT ON TABLE source_lookup IS 'Общий справочник источников травмы (Source + Secondary Source вместе)';


-- ---------------------------------------------------------------------------
-- Справочник отраслей NAICS (код строкой: 2–6 цифр, ведущие нули значимы)
-- ---------------------------------------------------------------------------

CREATE TABLE naics_lookup (
    code  varchar PRIMARY KEY,
    title varchar NOT NULL
);
COMMENT ON TABLE naics_lookup IS 'Справочник отраслей (NAICS code -> Industry title), из 2022 NAICS Structure (census.gov)';


-- ---------------------------------------------------------------------------
-- Факт-таблица
-- ---------------------------------------------------------------------------

CREATE TABLE injuries (
    id                    integer PRIMARY KEY,
    event_date            date,
    city                  varchar,
    state                 varchar,
    naics_code            varchar  REFERENCES naics_lookup (code),
    final_narrative       text,
    severity_code         smallint NOT NULL CHECK (severity_code BETWEEN 0 AND 7),
    nature_code           integer  REFERENCES nature_lookup (code),
    part_of_body_code     integer  REFERENCES body_part_lookup (code),
    event_code            integer  REFERENCES event_lookup (code),
    source_code           integer  REFERENCES source_lookup (code),
    secondary_source_code integer  REFERENCES source_lookup (code)
);
COMMENT ON TABLE injuries IS 'Факт-таблица: одна строка = один тяжёлый случай травмы (105 996 записей)';
COMMENT ON COLUMN injuries.id IS 'ID случая из отчёта OSHA';
COMMENT ON COLUMN injuries.naics_code IS 'Код отрасли, FK на naics_lookup.code; ~10% кодов из старых редакций NAICS';
COMMENT ON COLUMN injuries.severity_code IS 'Битовая маска: 4 = госпитализация, 2 = ампутация, 1 = потеря глаза (6 = госпитализация + ампутация)';
COMMENT ON COLUMN injuries.secondary_source_code IS 'Вторичный источник; NULL — не указан, 990/991 — заглушки OIICS';


-- ---------------------------------------------------------------------------
-- Индексы для аналитических запросов (SQL/01–08): фильтры по датам
-- и соединения со справочниками. PostgreSQL не создаёт индексы на FK сам.
-- ---------------------------------------------------------------------------

CREATE INDEX injuries_event_date_idx        ON injuries (event_date);
CREATE INDEX injuries_naics_code_idx        ON injuries (naics_code);
CREATE INDEX injuries_state_idx             ON injuries (state);
CREATE INDEX injuries_part_of_body_code_idx ON injuries (part_of_body_code);
CREATE INDEX injuries_event_code_idx        ON injuries (event_code);
CREATE INDEX injuries_source_code_idx       ON injuries (source_code);
CREATE INDEX injuries_nature_code_idx       ON injuries (nature_code);
