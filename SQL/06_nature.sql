-- ============================================================
--  Характер травмы (Nature): ЧТО случилось с организмом
--  (перелом, ампутация, ожог ...)
--  База: OSHA_db (PostgreSQL), таблицы injuries + nature_lookup
--
--  99.6% кодов относятся к разделу 1 «Травмы», поэтому деление по первой
--  цифре бесполезно. Кроме того, из-за разных редакций OIICS одно название
--  встречается под разными кодами ('Fractures' = 111 и 124). Поэтому:
--    6.1 — группировка по названию,
--    6.2 и 6.3 — по смысловым категориям (ключевые слова в названии).
-- ============================================================


-- 6.1. Топ-20 видов травм (группировка по названию)
SELECT
    n.title                                                 AS nature,
    STRING_AGG(DISTINCT n.code::text, ', ')                 AS codes,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all
FROM injuries i
JOIN nature_lookup n ON n.code = i.nature_code
GROUP BY n.title
ORDER BY cases DESC
LIMIT 20;


-- 6.2. Укрупнённые категории травм + доля госпитализаций
WITH categorized AS (
    SELECT
        i.*,
        CASE
            WHEN n.title ILIKE ANY (ARRAY['%amputat%', '%avulsion%', '%enucleation%'])
                                                               THEN 'Ампутации'
            WHEN n.title ILIKE '%fracture%'                    THEN 'Переломы'
            WHEN n.title ILIKE '%burn%'                        THEN 'Ожоги'
            WHEN n.title ILIKE ANY (ARRAY['%electrocution%', '%electric shock%'])
                                                               THEN 'Поражение электротоком'
            WHEN n.title ILIKE ANY (ARRAY['%heat%', '%hyperthermia%'])
                                                               THEN 'Тепловой удар / перегрев'
            WHEN n.title ILIKE ANY (ARRAY['%intracranial%', '%concussion%'])
                                                               THEN 'Черепно-мозговые травмы'
            WHEN n.title ILIKE ANY (ARRAY['%cuts%', '%laceration%', '%puncture%'])
                                                               THEN 'Раны (порезы, проколы)'
            WHEN n.title ILIKE '%crush%'                       THEN 'Размозжения'
            WHEN n.title ILIKE ANY (ARRAY['%dislocation%', '%sprain%', '%strain%'])
                                                               THEN 'Вывихи, растяжения'
            WHEN n.title ILIKE '%internal injur%'              THEN 'Внутренние повреждения'
            WHEN n.title ILIKE ANY (ARRAY['%soreness%', '%pain%'])
                                                               THEN 'Боль без уточнения'
            ELSE 'Прочее'
        END AS nature_category
    FROM injuries i
    JOIN nature_lookup n ON n.code = i.nature_code
)
SELECT
    nature_category,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all,
    ROUND(100.0 * COUNT(*) FILTER (WHERE severity_code & 4 > 0) / COUNT(*), 2) AS pct_hospitalized
FROM categorized
GROUP BY nature_category
ORDER BY cases DESC;


-- 6.3. Категория травмы → топ-3 части тела (например, «перелом → нога»)
WITH categorized AS (
    SELECT
        i.part_of_body_code,
        CASE
            WHEN n.title ILIKE ANY (ARRAY['%amputat%', '%avulsion%', '%enucleation%'])
                                                               THEN 'Ампутации'
            WHEN n.title ILIKE '%fracture%'                    THEN 'Переломы'
            WHEN n.title ILIKE '%burn%'                        THEN 'Ожоги'
            WHEN n.title ILIKE ANY (ARRAY['%electrocution%', '%electric shock%'])
                                                               THEN 'Поражение электротоком'
            WHEN n.title ILIKE ANY (ARRAY['%heat%', '%hyperthermia%'])
                                                               THEN 'Тепловой удар / перегрев'
            WHEN n.title ILIKE ANY (ARRAY['%intracranial%', '%concussion%'])
                                                               THEN 'Черепно-мозговые травмы'
            WHEN n.title ILIKE ANY (ARRAY['%cuts%', '%laceration%', '%puncture%'])
                                                               THEN 'Раны (порезы, проколы)'
            WHEN n.title ILIKE '%crush%'                       THEN 'Размозжения'
            WHEN n.title ILIKE ANY (ARRAY['%dislocation%', '%sprain%', '%strain%'])
                                                               THEN 'Вывихи, растяжения'
            WHEN n.title ILIKE '%internal injur%'              THEN 'Внутренние повреждения'
            WHEN n.title ILIKE ANY (ARRAY['%soreness%', '%pain%'])
                                                               THEN 'Боль без уточнения'
            ELSE 'Прочее'
        END AS nature_category
    FROM injuries i
    JOIN nature_lookup n ON n.code = i.nature_code
),
ranked AS (
    SELECT
        c.nature_category,
        b.title                                             AS body_part,
        COUNT(*)                                            AS cases,
        ROUND(100.0 * COUNT(*)
              / SUM(COUNT(*)) OVER (PARTITION BY c.nature_category), 2) AS pct_within_category,
        ROW_NUMBER() OVER (PARTITION BY c.nature_category ORDER BY COUNT(*) DESC) AS rn
    FROM categorized c
    JOIN body_part_lookup b ON b.code = c.part_of_body_code
    GROUP BY c.nature_category, b.title
)
SELECT nature_category, rn AS place, body_part, cases, pct_within_category
FROM ranked
WHERE rn <= 3
ORDER BY nature_category, rn;


-- 6.4. Категории травм по месяцам: доля в месяце и индекс к обычной доле
--      (100 = как обычно; 380 — доля в месяце в 3,8 раза выше обычной).
--      Какой тип травм характерен для каждого месяца — ноутбук 10_nature_by_month.
WITH categorized AS (
    SELECT
        EXTRACT(MONTH FROM i.event_date)::int AS month,
        CASE
            WHEN n.title ILIKE ANY (ARRAY['%amputat%', '%avulsion%', '%enucleation%'])
                                                               THEN 'Ампутации'
            WHEN n.title ILIKE '%fracture%'                    THEN 'Переломы'
            WHEN n.title ILIKE '%burn%'                        THEN 'Ожоги'
            WHEN n.title ILIKE ANY (ARRAY['%electrocution%', '%electric shock%'])
                                                               THEN 'Поражение электротоком'
            WHEN n.title ILIKE ANY (ARRAY['%heat%', '%hyperthermia%'])
                                                               THEN 'Тепловой удар / перегрев'
            WHEN n.title ILIKE ANY (ARRAY['%intracranial%', '%concussion%'])
                                                               THEN 'Черепно-мозговые травмы'
            WHEN n.title ILIKE ANY (ARRAY['%cuts%', '%laceration%', '%puncture%'])
                                                               THEN 'Раны (порезы, проколы)'
            WHEN n.title ILIKE '%crush%'                       THEN 'Размозжения'
            WHEN n.title ILIKE ANY (ARRAY['%dislocation%', '%sprain%', '%strain%'])
                                                               THEN 'Вывихи, растяжения'
            WHEN n.title ILIKE '%internal injur%'              THEN 'Внутренние повреждения'
            WHEN n.title ILIKE ANY (ARRAY['%soreness%', '%pain%'])
                                                               THEN 'Боль без уточнения'
            ELSE 'Прочее'
        END AS nature_category
    FROM injuries i
    JOIN nature_lookup n ON n.code = i.nature_code
),
by_month AS (
    SELECT
        nature_category,
        month,
        COUNT(*)                                            AS cases,
        100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY month)   AS pct_of_month,
        100.0 * SUM(COUNT(*)) OVER (PARTITION BY nature_category)
              / SUM(COUNT(*)) OVER ()                       AS pct_of_all
    FROM categorized
    GROUP BY nature_category, month
)
SELECT
    nature_category,
    month,
    cases,
    ROUND(pct_of_month, 2)                                  AS pct_of_month,
    ROUND(100 * pct_of_month / pct_of_all, 1)               AS month_index
FROM by_month
ORDER BY nature_category, month;
