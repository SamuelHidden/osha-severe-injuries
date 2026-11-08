-- ============================================================
--  Вопрос 4. Статистика случаев по годам 2015–2025
--  База: OSHA_db (PostgreSQL), таблица injuries
--
--  ВАЖНО: данные заканчиваются 30.11.2025, т.е. 2025 год неполный
--  (11 месяцев). Для честного сравнения смотрите avg_per_month.
--  severity_code — битовая маска: 4 = госпитализация, 2 = ампутация,
--  1 = потеря глаза.
-- ============================================================


-- 4.1. Число случаев по годам, изменение к прошлому году, среднее в месяц
WITH years AS (
    SELECT generate_series(2015, 2025) AS year
),
stats AS (
    SELECT
        EXTRACT(YEAR FROM event_date)::int                  AS year,
        COUNT(*)                                            AS cases,
        COUNT(DISTINCT DATE_TRUNC('month', event_date))     AS months_with_data
    FROM injuries
    WHERE event_date BETWEEN DATE '2015-01-01' AND DATE '2025-12-31'
    GROUP BY 1
)
SELECT
    y.year,
    COALESCE(s.cases, 0)                                    AS cases,
    s.months_with_data,
    ROUND(s.cases::numeric / NULLIF(s.months_with_data, 0), 1) AS avg_per_month,
    s.cases - LAG(s.cases) OVER (ORDER BY y.year)           AS diff_vs_prev_year,
    ROUND(100.0 * (s.cases - LAG(s.cases) OVER (ORDER BY y.year))
          / LAG(s.cases) OVER (ORDER BY y.year), 2)         AS pct_change_vs_prev_year,
    ROUND(100.0 * s.cases / SUM(s.cases) OVER (), 2)        AS pct_of_period
FROM years y
LEFT JOIN stats s ON s.year = y.year
ORDER BY y.year;


-- 4.2. Тяжесть последствий по годам
SELECT
    EXTRACT(YEAR FROM event_date)::int                      AS year,
    COUNT(*)                                                AS cases,
    COUNT(*) FILTER (WHERE severity_code & 4 > 0)           AS hospitalized,
    COUNT(*) FILTER (WHERE severity_code & 2 > 0)           AS amputations,
    COUNT(*) FILTER (WHERE severity_code & 1 > 0)           AS eye_loss,
    ROUND(100.0 * COUNT(*) FILTER (WHERE severity_code & 4 > 0) / COUNT(*), 2) AS pct_hospitalized,
    ROUND(100.0 * COUNT(*) FILTER (WHERE severity_code & 2 > 0) / COUNT(*), 2) AS pct_amputations
FROM injuries
WHERE event_date BETWEEN DATE '2015-01-01' AND DATE '2025-12-31'
GROUP BY 1
ORDER BY 1;


-- 4.3. Помесячная сводная таблица: строки — месяцы, столбцы — годы
SELECT
    EXTRACT(MONTH FROM event_date)::int                     AS month,
    COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM event_date) = 2015) AS "2015",
    COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM event_date) = 2016) AS "2016",
    COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM event_date) = 2017) AS "2017",
    COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM event_date) = 2018) AS "2018",
    COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM event_date) = 2019) AS "2019",
    COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM event_date) = 2020) AS "2020",
    COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM event_date) = 2021) AS "2021",
    COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM event_date) = 2022) AS "2022",
    COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM event_date) = 2023) AS "2023",
    COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM event_date) = 2024) AS "2024",
    COUNT(*) FILTER (WHERE EXTRACT(YEAR FROM event_date) = 2025) AS "2025",
    COUNT(*)                                                AS total
FROM injuries
WHERE event_date BETWEEN DATE '2015-01-01' AND DATE '2025-12-31'
GROUP BY 1
ORDER BY 1;


-- 4.4. Годы × крупнейшие секторы экономики (сводная таблица)
SELECT
    EXTRACT(YEAR FROM event_date)::int                      AS year,
    COUNT(*) FILTER (WHERE LEFT(naics_code, 2) = '23')                    AS construction,
    COUNT(*) FILTER (WHERE LEFT(naics_code, 2) IN ('31', '32', '33'))     AS manufacturing,
    COUNT(*) FILTER (WHERE LEFT(naics_code, 2) = '42')                    AS wholesale_trade,
    COUNT(*) FILTER (WHERE LEFT(naics_code, 2) IN ('44', '45'))           AS retail_trade,
    COUNT(*) FILTER (WHERE LEFT(naics_code, 2) IN ('48', '49'))           AS transport_warehousing,
    COUNT(*) FILTER (WHERE LEFT(naics_code, 2) = '56')                    AS admin_waste_services,
    COUNT(*) FILTER (WHERE LEFT(naics_code, 2) = '62')                    AS health_care,
    COUNT(*)                                                AS all_sectors
FROM injuries
WHERE event_date BETWEEN DATE '2015-01-01' AND DATE '2025-12-31'
GROUP BY 1
ORDER BY 1;
