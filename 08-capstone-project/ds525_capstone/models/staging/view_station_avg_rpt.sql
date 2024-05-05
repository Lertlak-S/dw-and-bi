SELECT station_id, name_th, name_en, province, AVG(pm25_value) avg_day, date, true AS indicater, pollutant
FROM `ds525-capstone-422206.capstone_aqgs_staging.view_air_quality_rpt` AS p
GROUP BY station_id, name_th, name_en, province, date, pollutant