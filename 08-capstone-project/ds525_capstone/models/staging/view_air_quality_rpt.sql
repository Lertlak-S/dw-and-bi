SELECT p.station_id, name_th, name_en, area_th, area_en, province, station_type, lat, long, 
       p.date , time, pm25_color_id, pm25_value, p.pollutant, 
FROM `ds525-capstone-422206.capstone_aqgs.pm25_trans` AS p
       INNER JOIN `ds525-capstone-422206.capstone_aqgs.station` AS s
       ON p.station_id = s.station_id