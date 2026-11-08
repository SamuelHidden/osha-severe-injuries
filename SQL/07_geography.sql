-- ============================================================
--  География: ГДЕ происходят травмы (штаты и города США)
--  База: OSHA_db (PostgreSQL), таблицы injuries + naics_lookup
--
--  ВАЖНО: это абсолютные числа. В крупных штатах (Техас, Флорида)
--  больше работников, поэтому и случаев больше — численности занятых
--  в базе нет, так что это не «уровень травматизма».
--  Кроме того, часть штатов работает по собственным планам (State Plan)
--  и отчитывается в федеральную OSHA не полностью.
-- ============================================================


-- 7.1. Штаты: число случаев, доля, тяжесть
SELECT
    RANK() OVER (ORDER BY COUNT(*) DESC)                    AS place,
    state,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all,
    ROUND(100.0 * COUNT(*) FILTER (WHERE severity_code & 4 > 0) / COUNT(*), 2) AS pct_hospitalized,
    ROUND(100.0 * COUNT(*) FILTER (WHERE severity_code & 2 > 0) / COUNT(*), 2) AS pct_amputation
FROM injuries
GROUP BY state
ORDER BY cases DESC;


-- 7.2. Топ-20 городов (город + штат, т.к. одноимённые города есть в разных штатах)
SELECT
    city,
    state,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all
FROM injuries
WHERE city <> 'unknown'
GROUP BY city, state
ORDER BY cases DESC
LIMIT 20;


-- 7.3. Ведущий сектор экономики в каждом штате
WITH sector AS (
    SELECT
        state,
        CASE
            WHEN LEFT(naics_code, 2) IN ('31', '32', '33') THEN '31-33'
            WHEN LEFT(naics_code, 2) IN ('44', '45')       THEN '44-45'
            WHEN LEFT(naics_code, 2) IN ('48', '49')       THEN '48-49'
            ELSE LEFT(naics_code, 2)
        END AS sector_code
    FROM injuries
),
ranked AS (
    SELECT
        s.state,
        COALESCE(n.title, 'Nonclassifiable / unknown')      AS top_sector,
        COUNT(*)                                            AS sector_cases,
        SUM(COUNT(*)) OVER (PARTITION BY s.state)           AS state_cases,
        ROW_NUMBER() OVER (PARTITION BY s.state ORDER BY COUNT(*) DESC) AS rn
    FROM sector s
    LEFT JOIN naics_lookup n ON n.code = s.sector_code
    GROUP BY s.state, n.title
)
SELECT
    state,
    state_cases,
    top_sector,
    sector_cases,
    ROUND(100.0 * sector_cases / state_cases, 2)            AS pct_of_state
FROM ranked
WHERE rn = 1
ORDER BY state_cases DESC;


-- 7.4. Как изменилось число случаев по штатам: 2015–2019 против 2021–2025
--      Сравниваем среднее в месяц (в 2025 году данные только за 11 месяцев:
--      2015–2019 = 60 месяцев, 2021–2025 = 59 месяцев). Штаты с >= 500 случаев.
WITH periods AS (
    SELECT
        state,
        COUNT(*) FILTER (WHERE event_date BETWEEN DATE '2015-01-01' AND DATE '2019-12-31') AS cases_2015_2019,
        COUNT(*) FILTER (WHERE event_date BETWEEN DATE '2021-01-01' AND DATE '2025-11-30') AS cases_2021_2025
    FROM injuries
    GROUP BY state
    HAVING COUNT(*) >= 500
)
SELECT
    state,
    cases_2015_2019,
    cases_2021_2025,
    ROUND(cases_2015_2019 / 60.0, 1)                        AS per_month_2015_2019,
    ROUND(cases_2021_2025 / 59.0, 1)                        AS per_month_2021_2025,
    ROUND(100.0 * (cases_2021_2025 / 59.0 - cases_2015_2019 / 60.0)
          / NULLIF(cases_2015_2019 / 60.0, 0), 2)           AS pct_change
FROM periods
ORDER BY pct_change;
