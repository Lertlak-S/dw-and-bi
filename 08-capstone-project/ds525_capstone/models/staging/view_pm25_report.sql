SELECT p.station_id, name_th, name_en, area_th, area_en, station_type, lat, long, 
       date , time, pm25_color_id, pm25_value, pollutant
FROM `ds525-capstone-422206.capstone_aqgs.pm25_trans` AS p
INNER JOIN `ds525-capstone-422206.capstone_aqgs.station` AS s
ON p.station_id = s.station_id
