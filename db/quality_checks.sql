-- Lab 2, section 2.5: overview queries and data quality checks.
-- Run them in pgAdmin (Query Tool on global_health) after the imports, or all at once
-- with:  psql -h localhost -U gh_user -d global_health -f db/quality_checks.sql
--
-- Each query starts with a "-- name:" line; the comment lines right after it say what
-- the query shows and the expected result. The queries of the lab handout are adapted
-- to this project's indicators and to its natural key, which also contains
-- residence_area (WHO splits PM2.5 into urban, rural and total).

-- name: overview_rows_per_indicator
-- Rows per indicator, with the first and last year stored.
SELECT i.code, i.name, COUNT(*) AS rows, MIN(o.year) AS first_year, MAX(o.year) AS last_year
FROM observation o JOIN indicator i USING (indicator_id)
GROUP BY i.code, i.name ORDER BY i.code;

-- name: overview_one_country
-- PM2.5 exposure (World Bank, OWID) and the chronic respiratory diseases death rate
-- (OWID, WHO Mortality Database) for Romania over time.
SELECT o.year,
       MAX(o.value) FILTER (WHERE i.code = 'EN.ATM.PM25.MC.M3')   AS pm25_worldbank,
       MAX(o.value) FILTER (WHERE i.code = 'OWID_PM25_EXPOSURE')  AS pm25_owid,
       MAX(o.value) FILTER (WHERE i.code = 'OWID_CRD_DEATH_RATE') AS crd_death_rate
FROM observation o JOIN indicator i USING (indicator_id)
WHERE o.country_iso3 = 'ROU' AND o.sex = 'BTSX' AND o.residence_area = 'TOTL'
GROUP BY o.year ORDER BY o.year;

-- name: overview_import_history
-- Import history, newest first.
SELECT * FROM import_log ORDER BY imported_at DESC;

-- name: check_1_countries
-- 1. Countries: one row per economy, no aggregates such as 'World'.
SELECT COUNT(*) AS countries, COUNT(DISTINCT region) AS regions
FROM country;

-- name: check_1b_aggregates
-- 1b. Expected: no rows (aggregates such as WLD, EAS or LMC are not countries).
SELECT iso3, name FROM country
WHERE iso3 IN ('WLD', 'EAS', 'ECS', 'LMC', 'HIC', 'EUU', 'AFE') OR region = 'Aggregates';

-- name: check_2_duplicates
-- 2. No duplicates on the natural key. Expected: no rows.
SELECT country_iso3, indicator_id, year, sex, residence_area, COUNT(*)
FROM observation
GROUP BY country_iso3, indicator_id, year, sex, residence_area
HAVING COUNT(*) > 1;

-- name: check_3_bounds
-- 3. Values inside the plausible bounds of each indicator (see etl/clean.py).
SELECT i.code, i.unit, MIN(o.value) AS min_value, MAX(o.value) AS max_value,
       ROUND(AVG(o.value), 2) AS avg_value
FROM observation o JOIN indicator i USING (indicator_id)
GROUP BY i.code, i.unit ORDER BY i.code;

-- name: check_4_sex_codes
-- 4. Only known sex codes. Expected: BTSX, MLE, FMLE.
SELECT sex, COUNT(*) FROM observation GROUP BY sex ORDER BY sex;

-- name: check_4b_residence_areas
-- 4b. Only known residence areas. Expected: TOTL, URB, RUR.
SELECT residence_area, COUNT(*) FROM observation GROUP BY residence_area ORDER BY residence_area;

-- name: check_5_missing_and_window
-- 5. No missing values and only years inside the window. Expected: 0, 0.
SELECT COUNT(*) FILTER (WHERE value IS NULL) AS null_values,
       COUNT(*) FILTER (WHERE value = 'NaN') AS nan_values,
       COUNT(*) FILTER (WHERE year NOT BETWEEN 2000 AND 2024) AS out_of_window
FROM observation;

-- name: check_6_rows_vs_last_import
-- 6. Rows stored match the rows reported by the last import of each indicator.
SELECT l.indicator_code, l.rows_loaded,
       (SELECT COUNT(*)
        FROM observation o JOIN indicator i USING (indicator_id)
        WHERE i.code = l.indicator_code) AS rows_stored
FROM import_log l
WHERE l.imported_at = (SELECT MAX(imported_at) FROM import_log x
                       WHERE x.indicator_code = l.indicator_code)
ORDER BY l.indicator_code;

-- name: check_7_coverage_gaps
-- 7. Countries without any chronic respiratory diseases death rate (coverage gaps).
SELECT c.iso3, c.name, c.region FROM country c
WHERE NOT EXISTS (
    SELECT 1 FROM observation o JOIN indicator i USING (indicator_id)
    WHERE o.country_iso3 = c.iso3 AND i.code = 'OWID_CRD_DEATH_RATE')
ORDER BY c.name;

-- name: check_7b_coverage_by_region
-- 7b. The same gaps counted per region.
SELECT c.region, COUNT(*) AS countries,
       COUNT(*) FILTER (WHERE NOT EXISTS (
           SELECT 1 FROM observation o JOIN indicator i USING (indicator_id)
           WHERE o.country_iso3 = c.iso3 AND i.code = 'OWID_CRD_DEATH_RATE')) AS without_crd
FROM country c
GROUP BY c.region ORDER BY c.region;

-- name: iqr_outliers_per_indicator
-- Task 2.2: rows flagged by the IQR rule (is_outlier) per indicator.
SELECT i.code, COUNT(*) AS rows,
       COUNT(*) FILTER (WHERE o.is_outlier) AS flagged,
       ROUND(100.0 * COUNT(*) FILTER (WHERE o.is_outlier) / COUNT(*), 1) AS flagged_pct
FROM observation o JOIN indicator i USING (indicator_id)
GROUP BY i.code ORDER BY i.code;

-- name: iqr_outliers_examples
-- Task 2.2: the highest flagged value of each indicator.
SELECT DISTINCT ON (i.code) i.code, o.country_iso3, c.name, o.year, o.value
FROM observation o
JOIN indicator i USING (indicator_id)
JOIN country c ON c.iso3 = o.country_iso3
WHERE o.is_outlier
ORDER BY i.code, o.value DESC;

-- name: comparison_one_country_year
-- Task 2.4: the stored values for Romania in 2019, one row per indicator.
SELECT s.name AS source, i.code, i.unit, o.year, o.sex, o.residence_area, o.value
FROM observation o
JOIN indicator i USING (indicator_id)
JOIN source s USING (source_id)
WHERE o.country_iso3 = 'ROU' AND o.year = 2019
ORDER BY s.name, i.code, o.residence_area;
