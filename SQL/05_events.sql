-- ============================================================
--  Тип происшествия (Event): КАК именно люди травмируются
--  База: OSHA_db (PostgreSQL), таблицы injuries + event_lookup
--
--  Коды OIICS иерархические: первая цифра = раздел
--  (4 — падения, 6 — контакт с предметами и оборудованием ...).
--  В данных смешаны разные редакции OIICS, поэтому одно и то же название
--  может встречаться под разными кодами — в 5.2 группируем по названию.
--  severity_code — битовая маска: 4 = госпитализация, 2 = ампутация,
--  1 = потеря глаза.
-- ============================================================


-- 5.1. Разделы типов происшествий + тяжесть последствий
WITH division(digit, name_ru, name_en) AS (
    VALUES ('1', 'Насилие, травмы от людей и животных',  'Violence and other injuries by persons or animals'),
           ('2', 'Транспортные происшествия',            'Transportation incidents'),
           ('3', 'Пожары и взрывы',                      'Fires and explosions'),
           ('4', 'Падения, поскальзывания, спотыкания',  'Falls, slips, trips'),
           ('5', 'Воздействие вредных веществ и среды',  'Exposure to harmful substances or environments'),
           ('6', 'Контакт с предметами и оборудованием', 'Contact with objects and equipment'),
           ('7', 'Перенапряжение и реакция организма',   'Overexertion and bodily reaction'),
           ('9', 'Не классифицировано',                  'Nonclassifiable')
)
SELECT
    d.name_ru                                               AS event_division,
    d.name_en,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all,
    ROUND(100.0 * COUNT(*) FILTER (WHERE i.severity_code & 4 > 0) / COUNT(*), 2) AS pct_hospitalized,
    ROUND(100.0 * COUNT(*) FILTER (WHERE i.severity_code & 2 > 0) / COUNT(*), 2) AS pct_amputation
FROM injuries i
JOIN division d ON d.digit = LEFT(i.event_code::text, 1)
GROUP BY d.name_ru, d.name_en
ORDER BY cases DESC;


-- 5.2. Топ-20 конкретных типов происшествий
--      (группировка по названию; codes — какие коды объединены)
SELECT
    e.title                                                 AS event,
    STRING_AGG(DISTINCT e.code::text, ', ')                 AS codes,
    COUNT(*)                                                AS cases,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)      AS pct_of_all,
    ROUND(100.0 * COUNT(*) FILTER (WHERE i.severity_code & 2 > 0) / COUNT(*), 2) AS pct_amputation
FROM injuries i
JOIN event_lookup e ON e.code = i.event_code
GROUP BY e.title
ORDER BY cases DESC
LIMIT 20;


-- 5.3. Тип происшествия × раздел тела (сводная таблица, число случаев)
WITH division(digit, name_ru) AS (
    VALUES ('1', 'Насилие, травмы от людей и животных'),
           ('2', 'Транспортные происшествия'),
           ('3', 'Пожары и взрывы'),
           ('4', 'Падения, поскальзывания, спотыкания'),
           ('5', 'Воздействие вредных веществ и среды'),
           ('6', 'Контакт с предметами и оборудованием'),
           ('7', 'Перенапряжение и реакция организма'),
           ('9', 'Не классифицировано')
)
SELECT
    d.name_ru                                                              AS event_division,
    COUNT(*) FILTER (WHERE LEFT(i.part_of_body_code::text, 1) = '1')       AS head,
    COUNT(*) FILTER (WHERE LEFT(i.part_of_body_code::text, 1) = '2')       AS neck,
    COUNT(*) FILTER (WHERE LEFT(i.part_of_body_code::text, 1) = '3')       AS trunk,
    COUNT(*) FILTER (WHERE LEFT(i.part_of_body_code::text, 1) = '4')       AS upper_extremities,
    COUNT(*) FILTER (WHERE LEFT(i.part_of_body_code::text, 1) = '5')       AS lower_extremities,
    COUNT(*) FILTER (WHERE LEFT(i.part_of_body_code::text, 1) = '6')       AS body_systems,
    COUNT(*) FILTER (WHERE LEFT(i.part_of_body_code::text, 1) = '8')       AS multiple_parts,
    COUNT(*) FILTER (WHERE LEFT(i.part_of_body_code::text, 1) = '9')       AS other,
    COUNT(*)                                                               AS total
FROM injuries i
JOIN division d ON d.digit = LEFT(i.event_code::text, 1)
GROUP BY d.digit, d.name_ru
ORDER BY total DESC;


-- 5.4. Разделы типов происшествий по годам 2015–2025 (сводная таблица)
SELECT
    EXTRACT(YEAR FROM event_date)::int                                     AS year,
    COUNT(*) FILTER (WHERE LEFT(event_code::text, 1) = '1')                AS violence,
    COUNT(*) FILTER (WHERE LEFT(event_code::text, 1) = '2')                AS transportation,
    COUNT(*) FILTER (WHERE LEFT(event_code::text, 1) = '3')                AS fire_explosion,
    COUNT(*) FILTER (WHERE LEFT(event_code::text, 1) = '4')                AS falls,
    COUNT(*) FILTER (WHERE LEFT(event_code::text, 1) = '5')                AS harmful_exposure,
    COUNT(*) FILTER (WHERE LEFT(event_code::text, 1) = '6')                AS contact_objects,
    COUNT(*) FILTER (WHERE LEFT(event_code::text, 1) = '7')                AS overexertion,
    COUNT(*) FILTER (WHERE LEFT(event_code::text, 1) = '9')                AS nonclassifiable,
    COUNT(*)                                                               AS total
FROM injuries
WHERE event_date BETWEEN DATE '2015-01-01' AND DATE '2025-12-31'
GROUP BY 1
ORDER BY 1;
