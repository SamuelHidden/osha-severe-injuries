-- ============================================================
--  Вопрос 1. Какие части тела чаще всего страдают?
--  База: OSHA_db (PostgreSQL), таблицы injuries + body_part_lookup
--
--  Коды частей тела — иерархия OIICS: первая цифра = раздел
--  (1 голова, 4 верхние конечности, 5 нижние ...), дальше уточнение
--  (4422 = кончики пальцев). Поэтому смотрим на двух уровнях:
--  точный код и укрупнённый раздел.
--
--  severity_code — битовая маска: 4 = госпитализация, 2 = ампутация,
--  1 = потеря глаза.
-- ============================================================


-- 1.1. Топ-20 частей тела (точный код OIICS) с долей от всех случаев
SELECT
    b.code                                                  AS body_part_code,
    b.title                                                 AS body_part,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all
FROM injuries i
JOIN body_part_lookup b ON b.code = i.part_of_body_code
GROUP BY b.code, b.title
ORDER BY cases DESC
LIMIT 20;


-- 1.2. Укрупнённые разделы тела (по первой цифре кода OIICS)
WITH division(digit, name_ru, name_en) AS (
    VALUES ('1', 'Голова',                     'Head'),
           ('2', 'Шея',                        'Neck'),
           ('3', 'Туловище',                   'Trunk'),
           ('4', 'Верхние конечности',         'Upper extremities'),
           ('5', 'Нижние конечности',          'Lower extremities'),
           ('6', 'Системы организма',          'Body systems'),
           ('8', 'Несколько частей тела',      'Multiple body parts'),
           ('9', 'Прочее / не классифицировано','Other, nonclassifiable')
)
SELECT
    d.name_ru                                               AS body_division,
    d.name_en,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all
FROM injuries i
JOIN division d ON d.digit = LEFT(i.part_of_body_code::text, 1)
GROUP BY d.name_ru, d.name_en
ORDER BY cases DESC;


-- 1.3. Какие части тела страдают при каждом виде тяжёлых последствий
--      (топ-5 для госпитализаций, ампутаций и потери глаза)
WITH outcomes AS (
    SELECT i.part_of_body_code, 'Госпитализация' AS outcome
    FROM injuries i WHERE i.severity_code & 4 > 0
    UNION ALL
    SELECT i.part_of_body_code, 'Ампутация'
    FROM injuries i WHERE i.severity_code & 2 > 0
    UNION ALL
    SELECT i.part_of_body_code, 'Потеря глаза'
    FROM injuries i WHERE i.severity_code & 1 > 0
),
ranked AS (
    SELECT
        o.outcome,
        b.title                                             AS body_part,
        COUNT(*)                                            AS cases,
        ROUND(100.0 * COUNT(*)
              / SUM(COUNT(*)) OVER (PARTITION BY o.outcome), 2) AS pct_within_outcome,
        ROW_NUMBER() OVER (PARTITION BY o.outcome ORDER BY COUNT(*) DESC) AS rn
    FROM outcomes o
    JOIN body_part_lookup b ON b.code = o.part_of_body_code
    GROUP BY o.outcome, b.title
)
SELECT outcome, rn AS place, body_part, cases, pct_within_outcome
FROM ranked
WHERE rn <= 5
ORDER BY outcome, rn;


-- 1.4. Топ-5 частей тела в каждом году 2015–2025
WITH by_year AS (
    SELECT
        EXTRACT(YEAR FROM i.event_date)::int                AS year,
        i.part_of_body_code
    FROM injuries i
    WHERE i.event_date BETWEEN DATE '2015-01-01' AND DATE '2025-12-31'
),
ranked AS (
    SELECT
        y.year,
        b.title                                             AS body_part,
        COUNT(*)                                            AS cases,
        ROW_NUMBER() OVER (PARTITION BY y.year ORDER BY COUNT(*) DESC) AS rn
    FROM by_year y
    JOIN body_part_lookup b ON b.code = y.part_of_body_code
    GROUP BY y.year, b.title
)
SELECT year, rn AS place, body_part, cases
FROM ranked
WHERE rn <= 5
ORDER BY year, rn;
