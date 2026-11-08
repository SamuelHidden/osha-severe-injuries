-- ============================================================
--  Вопрос 2. Какие Source и Secondary Source самые многочисленные?
--  База: OSHA_db (PostgreSQL), таблицы injuries + source_lookup
--
--  Source           — объект/вещество, непосредственно причинившее травму
--  Secondary Source — объект, способствовавший травме (может отсутствовать:
--                     secondary_source_code IS NULL)
--  Оба кода ссылаются на общий справочник source_lookup (иерархия OIICS:
--  первая цифра = раздел — химия, машины, транспорт ...).
--
--  Коды-заглушки, которые НЕ являются реальным источником:
--    990 = 'Source, secondary source unspecified'
--    991 = 'Secondary source not applicable'
--  Из рейтингов вторичных источников они исключены (см. 2.3).
-- ============================================================


-- 2.1. Топ-20 основных источников травмы (Source)
SELECT
    s.code                                                  AS source_code,
    s.title                                                 AS source,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all
FROM injuries i
JOIN source_lookup s ON s.code = i.source_code
GROUP BY s.code, s.title
ORDER BY cases DESC
LIMIT 20;


-- 2.2. Топ-20 вторичных источников (Secondary Source)
--      pct_of_with_secondary — доля среди случаев, где реальный вторичный
--      источник указан (без NULL и заглушек 990/991)
SELECT
    s.code                                                  AS secondary_source_code,
    s.title                                                 AS secondary_source,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_with_secondary
FROM injuries i
JOIN source_lookup s ON s.code = i.secondary_source_code
WHERE i.secondary_source_code NOT IN (990, 991)
GROUP BY s.code, s.title
ORDER BY cases DESC
LIMIT 20;


-- 2.3. Насколько часто вторичный источник вообще указан
SELECT
    COUNT(*)                                                AS all_cases,
    COUNT(*) FILTER (WHERE secondary_source_code NOT IN (990, 991)) AS with_real_secondary,
    COUNT(*) FILTER (WHERE secondary_source_code IN (990, 991))     AS placeholder_990_991,
    COUNT(*) FILTER (WHERE secondary_source_code IS NULL)           AS without_secondary,
    ROUND(100.0 * COUNT(*) FILTER (WHERE secondary_source_code NOT IN (990, 991))
          / COUNT(*), 2)                                    AS pct_with_real_secondary
FROM injuries;


-- 2.4. Разделы источников (первая цифра OIICS): Source и Secondary Source рядом
WITH division(digit, name_ru, name_en) AS (
    VALUES ('1', 'Химические вещества и продукты',      'Chemicals and chemical products'),
           ('2', 'Тара, мебель, оборудование помещений','Containers, furniture, and fixtures'),
           ('3', 'Машины и механизмы',                  'Machinery'),
           ('4', 'Детали и материалы',                  'Parts and materials'),
           ('5', 'Люди, растения, животные, минералы',  'Persons, plants, animals, and minerals'),
           ('6', 'Конструкции и поверхности',           'Structures and surfaces'),
           ('7', 'Инструменты, приборы, оборудование',  'Tools, instruments, and equipment'),
           ('8', 'Транспортные средства',               'Vehicles'),
           ('9', 'Прочие источники',                    'Other sources')
),
counts AS (
    SELECT LEFT(source_code::text, 1) AS digit, 'source' AS kind FROM injuries
    UNION ALL
    SELECT LEFT(secondary_source_code::text, 1), 'secondary' FROM injuries
    WHERE secondary_source_code NOT IN (990, 991)
)
SELECT
    d.name_ru                                               AS source_division,
    d.name_en,
    COUNT(*) FILTER (WHERE c.kind = 'source')               AS as_source,
    ROUND(100.0 * COUNT(*) FILTER (WHERE c.kind = 'source')
          / SUM(COUNT(*) FILTER (WHERE c.kind = 'source')) OVER (), 2)    AS pct_source,
    COUNT(*) FILTER (WHERE c.kind = 'secondary')            AS as_secondary,
    ROUND(100.0 * COUNT(*) FILTER (WHERE c.kind = 'secondary')
          / SUM(COUNT(*) FILTER (WHERE c.kind = 'secondary')) OVER (), 2) AS pct_secondary
FROM counts c
JOIN division d ON d.digit = c.digit
GROUP BY d.digit, d.name_ru, d.name_en
ORDER BY as_source DESC;


-- 2.5. Топ-20 источников по общему числу упоминаний
--      (как основной ИЛИ как вторичный источник — справочник общий)
SELECT
    s.code,
    s.title                                                 AS source,
    COUNT(*) FILTER (WHERE u.kind = 'source')               AS as_source,
    COUNT(*) FILTER (WHERE u.kind = 'secondary')            AS as_secondary,
    COUNT(*)                                                AS total_mentions
FROM (
    SELECT source_code AS code, 'source' AS kind FROM injuries
    UNION ALL
    SELECT secondary_source_code, 'secondary' FROM injuries
    WHERE secondary_source_code NOT IN (990, 991)
) u
JOIN source_lookup s ON s.code = u.code
GROUP BY s.code, s.title
ORDER BY total_mentions DESC
LIMIT 20;


-- 2.6. Топ-15 самых частых сочетаний Source + Secondary Source
SELECT
    s1.title                                                AS source,
    s2.title                                                AS secondary_source,
    COUNT(*)                                                AS cases
FROM injuries i
JOIN source_lookup s1 ON s1.code = i.source_code
JOIN source_lookup s2 ON s2.code = i.secondary_source_code
WHERE i.secondary_source_code NOT IN (990, 991)
GROUP BY s1.title, s2.title
ORDER BY cases DESC
LIMIT 15;


-- 2.7. Топ-5 Source и топ-5 Secondary Source в каждом году 2015–2025
--      В одной строке — источники, занявшие одно и то же место в своём рейтинге
--      (это НЕ пара из одного случая). Secondary Source — без NULL и заглушек 990/991.
WITH src_ranked AS (
    SELECT
        EXTRACT(YEAR FROM i.event_date)::int                AS year,
        s.title                                             AS source,
        COUNT(*)                                            AS source_count,
        ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM i.event_date)::int
                           ORDER BY COUNT(*) DESC)          AS rn
    FROM injuries i
    JOIN source_lookup s ON s.code = i.source_code
    WHERE i.event_date BETWEEN DATE '2015-01-01' AND DATE '2025-12-31'
    GROUP BY EXTRACT(YEAR FROM i.event_date)::int, s.title
),
sec_ranked AS (
    SELECT
        EXTRACT(YEAR FROM i.event_date)::int                AS year,
        s.title                                             AS secondary_source,
        COUNT(*)                                            AS secondary_source_count,
        ROW_NUMBER() OVER (PARTITION BY EXTRACT(YEAR FROM i.event_date)::int
                           ORDER BY COUNT(*) DESC)          AS rn
    FROM injuries i
    JOIN source_lookup s ON s.code = i.secondary_source_code
    WHERE i.event_date BETWEEN DATE '2015-01-01' AND DATE '2025-12-31'
      AND i.secondary_source_code NOT IN (990, 991)
    GROUP BY EXTRACT(YEAR FROM i.event_date)::int, s.title
)
SELECT
    COALESCE(p.year, q.year)                                AS year,
    COALESCE(p.rn, q.rn)                                    AS place,
    p.source,
    p.source_count,
    q.secondary_source,
    q.secondary_source_count
FROM (SELECT * FROM src_ranked WHERE rn <= 5) p
FULL JOIN (SELECT * FROM sec_ranked WHERE rn <= 5) q
       ON q.year = p.year AND q.rn = p.rn
ORDER BY year, place;
