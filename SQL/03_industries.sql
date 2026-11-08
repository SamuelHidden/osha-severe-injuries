-- ============================================================
--  Вопрос 3. В каких отраслях чаще всего происходят травмы?
--  База: OSHA_db (PostgreSQL), таблицы injuries + naics_lookup
--
--  NAICS — иерархический код: 2 цифры = сектор, 3 = подсектор,
--  6 = конкретная отрасль. Некоторые секторы в справочнике 2022
--  заданы диапазоном: 31-33 (обрабатывающая промышленность),
--  44-45 (розничная торговля), 48-49 (транспорт и склады).
--  ~10% кодов в данных — из старых редакций NAICS (2012/2017), в
--  справочнике у них заглушка 'Not in 2022 NAICS (legacy code)', поэтому
--  отрасли удобнее сравнивать по сектору/подсектору (префикс кода).
-- ============================================================


-- 3.1. Секторы экономики (2 цифры NAICS)
WITH sector AS (
    SELECT
        CASE
            WHEN LEFT(naics_code, 2) IN ('31', '32', '33') THEN '31-33'
            WHEN LEFT(naics_code, 2) IN ('44', '45')       THEN '44-45'
            WHEN LEFT(naics_code, 2) IN ('48', '49')       THEN '48-49'
            ELSE LEFT(naics_code, 2)
        END AS sector_code
    FROM injuries
)
SELECT
    COALESCE(s.sector_code, 'нет кода')                     AS sector_code,
    COALESCE(n.title, 'Nonclassifiable / unknown')          AS sector,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all
FROM sector s
LEFT JOIN naics_lookup n ON n.code = s.sector_code
GROUP BY s.sector_code, n.title
ORDER BY cases DESC;


-- 3.2. Топ-20 подсекторов (3 цифры NAICS)
SELECT
    LEFT(i.naics_code, 3)                                   AS subsector_code,
    COALESCE(n.title, 'Unknown')                            AS subsector,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all
FROM injuries i
LEFT JOIN naics_lookup n ON n.code = LEFT(i.naics_code, 3)
WHERE LENGTH(i.naics_code) >= 3
GROUP BY LEFT(i.naics_code, 3), n.title
ORDER BY cases DESC
LIMIT 20;


-- 3.3. Топ-20 конкретных отраслей (полный 6-значный код NAICS)
SELECT
    i.naics_code,
    n.title                                                 AS industry,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all
FROM injuries i
JOIN naics_lookup n ON n.code = i.naics_code
WHERE LENGTH(i.naics_code) = 6
GROUP BY i.naics_code, n.title
ORDER BY cases DESC
LIMIT 20;


-- 3.4. Тяжесть последствий по секторам: доля госпитализаций,
--      ампутаций и потери глаза (секторы с числом случаев >= 500)
WITH sector AS (
    SELECT
        CASE
            WHEN LEFT(naics_code, 2) IN ('31', '32', '33') THEN '31-33'
            WHEN LEFT(naics_code, 2) IN ('44', '45')       THEN '44-45'
            WHEN LEFT(naics_code, 2) IN ('48', '49')       THEN '48-49'
            ELSE LEFT(naics_code, 2)
        END AS sector_code,
        severity_code
    FROM injuries
)
SELECT
    n.title                                                 AS sector,
    COUNT(*)                                                AS cases,
    COUNT(*) FILTER (WHERE severity_code & 4 > 0)           AS hospitalized,
    COUNT(*) FILTER (WHERE severity_code & 2 > 0)           AS amputations,
    COUNT(*) FILTER (WHERE severity_code & 1 > 0)           AS eye_loss,
    ROUND(100.0 * COUNT(*) FILTER (WHERE severity_code & 2 > 0) / COUNT(*), 2) AS pct_amputation
FROM sector s
JOIN naics_lookup n ON n.code = s.sector_code
GROUP BY n.title
HAVING COUNT(*) >= 500
ORDER BY pct_amputation DESC;


-- 3.5. Топ-3 сектора в каждом году 2015–2025
WITH sector AS (
    SELECT
        EXTRACT(YEAR FROM event_date)::int AS year,
        CASE
            WHEN LEFT(naics_code, 2) IN ('31', '32', '33') THEN '31-33'
            WHEN LEFT(naics_code, 2) IN ('44', '45')       THEN '44-45'
            WHEN LEFT(naics_code, 2) IN ('48', '49')       THEN '48-49'
            ELSE LEFT(naics_code, 2)
        END AS sector_code
    FROM injuries
    WHERE event_date BETWEEN DATE '2015-01-01' AND DATE '2025-12-31'
),
ranked AS (
    SELECT
        s.year,
        n.title                                             AS sector,
        COUNT(*)                                            AS cases,
        ROUND(100.0 * COUNT(*)
              / SUM(COUNT(*)) OVER (PARTITION BY s.year), 2) AS pct_of_year,
        ROW_NUMBER() OVER (PARTITION BY s.year ORDER BY COUNT(*) DESC) AS rn
    FROM sector s
    JOIN naics_lookup n ON n.code = s.sector_code
    GROUP BY s.year, n.title
)
SELECT year, rn AS place, sector, cases, pct_of_year
FROM ranked
WHERE rn <= 3
ORDER BY year, rn;
