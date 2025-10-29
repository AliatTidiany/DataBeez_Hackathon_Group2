-- =====================================================
-- Requêtes d'Analyse pour les Données GEE Sénégal
-- =====================================================

-- 1. Vue d'ensemble des données
-- =============================

-- Statistiques générales par région
SELECT 
    region,
    COUNT(*) as total_records,
    MIN(date) as first_date,
    MAX(date) as last_date,
    AVG(data_completeness_score) as avg_completeness,
    AVG(temperature_era5_c) as avg_temp_c,
    SUM(precipitation_era5_mm) as total_precip_mm,
    AVG(ndvi_modis) as avg_ndvi
FROM gee_senegal_agro_data
GROUP BY region
ORDER BY region;

-- 2. Analyse temporelle
-- ====================

-- Tendances mensuelles moyennes (toutes années confondues)
SELECT 
    month,
    AVG(temperature_era5_c) as avg_temp_c,
    AVG(precipitation_era5_mm) as avg_precip_mm,
    AVG(ndvi_modis) as avg_ndvi,
    AVG(soil_moisture_smap_percent) as avg_soil_moisture
FROM gee_senegal_agro_data
WHERE data_completeness_score > 0.5
GROUP BY month
ORDER BY month;

-- Évolution annuelle par région
SELECT 
    region,
    year,
    AVG(temperature_era5_c) as avg_temp_c,
    SUM(precipitation_era5_mm) as total_precip_mm,
    AVG(ndvi_modis) as avg_ndvi,
    AVG(drought_index) as avg_drought_index
FROM gee_senegal_agro_data
WHERE data_completeness_score > 0.7
GROUP BY region, year
ORDER BY region, year;

-- 3. Analyse spatiale
-- ==================

-- Comparaison des régions (moyennes générales)
SELECT 
    region,
    ROUND(AVG(temperature_era5_c), 2) as avg_temp_c,
    ROUND(AVG(precipitation_era5_mm), 3) as avg_daily_precip_mm,
    ROUND(AVG(ndvi_modis), 3) as avg_ndvi,
    ROUND(AVG(soil_moisture_smap_percent), 2) as avg_soil_moisture,
    ROUND(AVG(wind_speed_ms), 2) as avg_wind_speed,
    ROUND(AVG(solar_radiation_mj_m2), 2) as avg_solar_radiation
FROM gee_senegal_agro_data
WHERE data_completeness_score > 0.5
GROUP BY region
ORDER BY avg_temp_c DESC;

-- Gradient climatique Nord-Sud
SELECT 
    region,
    ROUND(AVG(latitude), 4) as avg_latitude,
    ROUND(AVG(temperature_era5_c), 2) as avg_temp_c,
    ROUND(AVG(precipitation_era5_mm), 3) as avg_precip_mm
FROM gee_senegal_agro_data
WHERE data_completeness_score > 0.5
GROUP BY region
ORDER BY avg_latitude DESC;

-- 4. Analyse saisonnière
-- =====================

-- Comparaison saison sèche vs saison des pluies
SELECT 
    region,
    season,
    COUNT(*) as record_count,
    ROUND(AVG(temperature_era5_c), 2) as avg_temp_c,
    ROUND(AVG(precipitation_era5_mm), 3) as avg_precip_mm,
    ROUND(AVG(ndvi_modis), 3) as avg_ndvi,
    ROUND(AVG(humidity_index), 3) as avg_humidity
FROM gee_senegal_agro_data
WHERE data_completeness_score > 0.5
GROUP BY region, season
ORDER BY region, season;

-- Mois les plus chauds et les plus froids par région
WITH temp_stats AS (
    SELECT 
        region,
        month,
        AVG(temperature_era5_c) as avg_temp
    FROM gee_senegal_agro_data
    WHERE temperature_era5_c IS NOT NULL
    GROUP BY region, month
),
region_extremes AS (
    SELECT 
        region,
        MAX(avg_temp) as max_temp,
        MIN(avg_temp) as min_temp
    FROM temp_stats
    GROUP BY region
)
SELECT 
    ts.region,
    ts.month as hottest_month,
    ROUND(re.max_temp, 2) as max_temp_c,
    ts2.month as coldest_month,
    ROUND(re.min_temp, 2) as min_temp_c
FROM region_extremes re
JOIN temp_stats ts ON re.region = ts.region AND re.max_temp = ts.avg_temp
JOIN temp_stats ts2 ON re.region = ts2.region AND re.min_temp = ts2.avg_temp
ORDER BY ts.region;

-- 5. Analyse de la végétation
-- ===========================

-- Évolution saisonnière du NDVI
SELECT 
    region,
    month,
    COUNT(*) as data_points,
    ROUND(AVG(ndvi_modis), 3) as avg_ndvi,
    ROUND(STDDEV(ndvi_modis), 3) as stddev_ndvi,
    ROUND(MIN(ndvi_modis), 3) as min_ndvi,
    ROUND(MAX(ndvi_modis), 3) as max_ndvi
FROM gee_senegal_agro_data
WHERE ndvi_modis IS NOT NULL
GROUP BY region, month
ORDER BY region, month;

-- Corrélation NDVI vs Précipitations
SELECT 
    region,
    ROUND(CORR(ndvi_modis, precipitation_era5_mm), 3) as ndvi_precip_correlation,
    ROUND(CORR(ndvi_modis, temperature_era5_c), 3) as ndvi_temp_correlation,
    ROUND(CORR(ndvi_modis, soil_moisture_smap_percent), 3) as ndvi_soil_correlation
FROM gee_senegal_agro_data
WHERE ndvi_modis IS NOT NULL 
AND precipitation_era5_mm IS NOT NULL
AND temperature_era5_c IS NOT NULL
GROUP BY region
ORDER BY ndvi_precip_correlation DESC;

-- 6. Analyse des extrêmes climatiques
-- ===================================

-- Événements de sécheresse (faibles précipitations + haute température)
SELECT 
    region,
    date,
    temperature_era5_c,
    precipitation_era5_mm,
    drought_index,
    ndvi_modis
FROM gee_senegal_agro_data
WHERE drought_index > (
    SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY drought_index)
    FROM gee_senegal_agro_data
    WHERE drought_index IS NOT NULL
)
ORDER BY drought_index DESC, region, date;

-- Jours les plus chauds par région et année
WITH daily_max_temp AS (
    SELECT 
        region,
        year,
        MAX(temperature_era5_c) as max_temp_year,
        date
    FROM gee_senegal_agro_data
    WHERE temperature_era5_c IS NOT NULL
    GROUP BY region, year, date
),
yearly_max AS (
    SELECT 
        region,
        year,
        MAX(max_temp_year) as absolute_max_temp
    FROM daily_max_temp
    GROUP BY region, year
)
SELECT 
    dmt.region,
    dmt.year,
    dmt.date,
    ROUND(ym.absolute_max_temp, 2) as max_temp_c
FROM yearly_max ym
JOIN daily_max_temp dmt ON ym.region = dmt.region 
    AND ym.year = dmt.year 
    AND ym.absolute_max_temp = dmt.max_temp_year
ORDER BY dmt.region, dmt.year;

-- 7. Qualité des données
-- ======================

-- Disponibilité des données par source et région
SELECT 
    region,
    COUNT(*) as total_records,
    ROUND(AVG(CASE WHEN temperature_era5_c IS NOT NULL THEN 1 ELSE 0 END) * 100, 1) as temp_availability_pct,
    ROUND(AVG(CASE WHEN precipitation_era5_mm IS NOT NULL THEN 1 ELSE 0 END) * 100, 1) as precip_availability_pct,
    ROUND(AVG(CASE WHEN ndvi_modis IS NOT NULL THEN 1 ELSE 0 END) * 100, 1) as ndvi_availability_pct,
    ROUND(AVG(CASE WHEN soil_moisture_smap_percent IS NOT NULL THEN 1 ELSE 0 END) * 100, 1) as soil_availability_pct,
    ROUND(AVG(data_completeness_score) * 100, 1) as avg_completeness_pct
FROM gee_senegal_agro_data
GROUP BY region
ORDER BY avg_completeness_pct DESC;

-- Lacunes temporelles dans les données
SELECT 
    region,
    date,
    LAG(date) OVER (PARTITION BY region ORDER BY date) as prev_date,
    date - LAG(date) OVER (PARTITION BY region ORDER BY date) as gap_days
FROM gee_senegal_agro_data
WHERE data_completeness_score > 0.5
ORDER BY region, date;

-- 8. Données pour la modélisation
-- ===============================

-- Dataset propre pour machine learning (dernières 2 années)
SELECT 
    region,
    date,
    year,
    month,
    day_of_year,
    temperature_era5_c,
    precipitation_era5_mm,
    precipitation_cumulative_30d,
    temperature_mean_7d,
    ndvi_modis,
    ndvi_anomaly,
    soil_moisture_smap_percent,
    growing_degree_days,
    drought_index,
    is_rainy_season,
    wind_speed_ms,
    solar_radiation_mj_m2
FROM gee_senegal_agro_data
WHERE data_completeness_score > 0.8
AND year >= 2023
AND temperature_era5_c IS NOT NULL
AND precipitation_era5_mm IS NOT NULL
ORDER BY region, date;

-- Matrice de corrélation des variables principales
SELECT 
    'temperature_era5_c' as variable,
    ROUND(CORR(temperature_era5_c, precipitation_era5_mm), 3) as corr_precip,
    ROUND(CORR(temperature_era5_c, ndvi_modis), 3) as corr_ndvi,
    ROUND(CORR(temperature_era5_c, soil_moisture_smap_percent), 3) as corr_soil,
    ROUND(CORR(temperature_era5_c, wind_speed_ms), 3) as corr_wind
FROM gee_senegal_agro_data
WHERE data_completeness_score > 0.7

UNION ALL

SELECT 
    'precipitation_era5_mm' as variable,
    ROUND(CORR(precipitation_era5_mm, temperature_era5_c), 3) as corr_temp,
    ROUND(CORR(precipitation_era5_mm, ndvi_modis), 3) as corr_ndvi,
    ROUND(CORR(precipitation_era5_mm, soil_moisture_smap_percent), 3) as corr_soil,
    ROUND(CORR(precipitation_era5_mm, wind_speed_ms), 3) as corr_wind
FROM gee_senegal_agro_data
WHERE data_completeness_score > 0.7;

-- 9. Requêtes d'agrégation pour tableaux de bord
-- ==============================================

-- Résumé mensuel pour dashboard
CREATE OR REPLACE VIEW dashboard_monthly_summary AS
SELECT 
    region,
    year,
    month,
    COUNT(*) as record_count,
    ROUND(AVG(temperature_era5_c), 1) as avg_temp_c,
    ROUND(SUM(precipitation_era5_mm), 1) as total_precip_mm,
    ROUND(AVG(ndvi_modis), 3) as avg_ndvi,
    ROUND(AVG(soil_moisture_smap_percent), 1) as avg_soil_moisture,
    ROUND(AVG(drought_index), 2) as avg_drought_index,
    ROUND(AVG(data_completeness_score) * 100, 1) as completeness_pct
FROM gee_senegal_agro_data
GROUP BY region, year, month
ORDER BY region, year, month;

-- Indicateurs clés par région (KPI)
CREATE OR REPLACE VIEW dashboard_region_kpi AS
SELECT 
    region,
    COUNT(*) as total_observations,
    ROUND(AVG(temperature_era5_c), 1) as avg_temperature_c,
    ROUND(AVG(precipitation_era5_mm) * 365, 0) as annual_precip_estimate_mm,
    ROUND(AVG(ndvi_modis), 3) as avg_vegetation_index,
    ROUND(AVG(drought_index), 2) as avg_drought_risk,
    CASE 
        WHEN AVG(drought_index) > 2 THEN 'High Risk'
        WHEN AVG(drought_index) > 1.5 THEN 'Medium Risk'
        ELSE 'Low Risk'
    END as drought_risk_category,
    ROUND(AVG(data_completeness_score) * 100, 1) as data_quality_pct
FROM gee_senegal_agro_data
WHERE data_completeness_score > 0.5
GROUP BY region
ORDER BY avg_drought_risk DESC;