-- ============================================================
--  Причины травм: типичные сценарии, портреты отраслей, правило 80/20
--  База: OSHA_db (PostgreSQL), все 6 таблиц
--
--  Здесь данные из разных справочников сводятся вместе, чтобы понять,
--  на чём сосредоточить профилактику.
-- ============================================================


-- 8.1. Топ-25 сценариев «тип происшествия → источник → часть тела»
SELECT
    e.title                                                 AS event,
    s.title                                                 AS source,
    b.title                                                 AS body_part,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all,
    ROUND(100.0 * COUNT(*) FILTER (WHERE i.severity_code & 2 > 0) / COUNT(*), 2) AS pct_amputation
FROM injuries i
JOIN event_lookup     e ON e.code = i.event_code
JOIN source_lookup    s ON s.code = i.source_code
JOIN body_part_lookup b ON b.code = i.part_of_body_code
GROUP BY e.title, s.title, b.title
ORDER BY cases DESC
LIMIT 25;


-- 8.2. Портрет отрасли: для 8 крупнейших секторов — главный тип происшествия,
--      главный источник, главная часть тела и главный вид травмы
--      (в скобках *_pct — доля внутри сектора)
WITH base AS (
    SELECT
        CASE
            WHEN LEFT(naics_code, 2) IN ('31', '32', '33') THEN '31-33'
            WHEN LEFT(naics_code, 2) IN ('44', '45')       THEN '44-45'
            WHEN LEFT(naics_code, 2) IN ('48', '49')       THEN '48-49'
            ELSE LEFT(naics_code, 2)
        END AS sector_code,
        event_code, source_code, part_of_body_code, nature_code
    FROM injuries
),
top_sectors AS (
    SELECT b.sector_code, n.title AS sector, COUNT(*) AS cases
    FROM base b
    JOIN naics_lookup n ON n.code = b.sector_code
    GROUP BY b.sector_code, n.title
    ORDER BY cases DESC
    LIMIT 8
),
ev AS (
    SELECT b.sector_code, e.title, COUNT(*) AS n,
           ROW_NUMBER() OVER (PARTITION BY b.sector_code ORDER BY COUNT(*) DESC) AS rn
    FROM base b JOIN event_lookup e ON e.code = b.event_code
    GROUP BY b.sector_code, e.title
),
src AS (
    SELECT b.sector_code, s.title, COUNT(*) AS n,
           ROW_NUMBER() OVER (PARTITION BY b.sector_code ORDER BY COUNT(*) DESC) AS rn
    FROM base b JOIN source_lookup s ON s.code = b.source_code
    GROUP BY b.sector_code, s.title
),
bp AS (
    SELECT b.sector_code, p.title, COUNT(*) AS n,
           ROW_NUMBER() OVER (PARTITION BY b.sector_code ORDER BY COUNT(*) DESC) AS rn
    FROM base b JOIN body_part_lookup p ON p.code = b.part_of_body_code
    GROUP BY b.sector_code, p.title
),
nat AS (
    SELECT b.sector_code, n.title, COUNT(*) AS n,
           ROW_NUMBER() OVER (PARTITION BY b.sector_code ORDER BY COUNT(*) DESC) AS rn
    FROM base b JOIN nature_lookup n ON n.code = b.nature_code
    GROUP BY b.sector_code, n.title
)
SELECT
    t.sector,
    t.cases,
    ev.title                                    AS top_event,
    ROUND(100.0 * ev.n  / t.cases, 1)           AS event_pct,
    src.title                                   AS top_source,
    ROUND(100.0 * src.n / t.cases, 1)           AS source_pct,
    bp.title                                    AS top_body_part,
    ROUND(100.0 * bp.n  / t.cases, 1)           AS body_part_pct,
    nat.title                                   AS top_nature,
    ROUND(100.0 * nat.n / t.cases, 1)           AS nature_pct
FROM top_sectors t
JOIN ev  ON ev.sector_code  = t.sector_code AND ev.rn  = 1
JOIN src ON src.sector_code = t.sector_code AND src.rn = 1
JOIN bp  ON bp.sector_code  = t.sector_code AND bp.rn  = 1
JOIN nat ON nat.sector_code = t.sector_code AND nat.rn = 1
ORDER BY t.cases DESC;


-- 8.3. Парето по источникам: какие источники вместе дают 80% всех случаев
--      (список обрывается, когда накопленная доля доходит до 80%)
WITH per_source AS (
    SELECT s.code, s.title, COUNT(*) AS cases
    FROM injuries i
    JOIN source_lookup s ON s.code = i.source_code
    GROUP BY s.code, s.title
),
cumulative AS (
    SELECT
        code,
        title,
        cases,
        SUM(cases) OVER (ORDER BY cases DESC, code)         AS cum_cases,
        SUM(cases) OVER ()                                  AS total
    FROM per_source
)
SELECT
    ROW_NUMBER() OVER (ORDER BY cases DESC, code)           AS place,
    code,
    title                                                   AS source,
    cases,
    ROUND(100.0 * cases / total, 2)                         AS pct,
    ROUND(100.0 * cum_cases / total, 2)                     AS cum_pct
FROM cumulative
WHERE cum_cases - cases < 0.8 * total
ORDER BY place;


-- 8.4. Правило 80/20 сводно: сколько кодов в каждом справочнике
--      покрывают 80% случаев (чем меньше доля кодов — тем сильнее концентрация)
WITH per_code AS (
    SELECT 'Source (источник)'            AS dimension, source_code::text        AS code, COUNT(*) AS cases FROM injuries GROUP BY source_code
    UNION ALL
    SELECT 'Event (тип происшествия)',                  event_code::text,                 COUNT(*)          FROM injuries GROUP BY event_code
    UNION ALL
    SELECT 'Part of body (часть тела)',                 part_of_body_code::text,          COUNT(*)          FROM injuries GROUP BY part_of_body_code
    UNION ALL
    SELECT 'Nature (характер травмы)',                  nature_code::text,                COUNT(*)          FROM injuries GROUP BY nature_code
    UNION ALL
    SELECT 'NAICS (отрасль, полный код)',               naics_code,                       COUNT(*)          FROM injuries GROUP BY naics_code
),
cumulative AS (
    SELECT
        dimension,
        cases,
        SUM(cases) OVER (PARTITION BY dimension ORDER BY cases DESC, code) AS cum_cases,
        SUM(cases) OVER (PARTITION BY dimension)                           AS total
    FROM per_code
)
SELECT
    dimension,
    COUNT(*)                                                AS codes_in_data,
    COUNT(*) FILTER (WHERE cum_cases - cases < 0.8 * total) AS codes_for_80pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE cum_cases - cases < 0.8 * total)
          / COUNT(*), 2)                                    AS pct_of_codes
FROM cumulative
GROUP BY dimension
ORDER BY pct_of_codes;
