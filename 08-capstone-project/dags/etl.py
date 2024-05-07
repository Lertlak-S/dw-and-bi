import json
import glob
import os
import requests
import logging
import pickle
import pandas as pd

from airflow import DAG
from airflow.utils import timezone
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.transfers.local_to_gcs import LocalFilesystemToGCSOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateEmptyDatasetOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryExecuteQueryOperator
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import List

data_path = '/opt/airflow/dags/data'
data_folder = data_path + '/' # local dir
clean_folder = data_folder + 'cleaned' 

def _get_files():
    if not os.path.exists(data_path):
        os.makedirs(data_path)
    exit_file_name = os.listdir(data_folder)
    url = 'https://opendata.onde.go.th/dataset/14-pm-25'
    links = []
    req = requests.get(url, verify=False)
    req.encoding = 'utf-8'
    soup = BeautifulSoup(req.text, 'html.parser')
    #print(soup.prettify())
    og = soup.find('meta', property='og:url')
    base = urlparse(url)
    for link in soup.find_all('a'):
        current_link = link.get('href')
        if str(current_link).endswith('csv'):
            links.append(current_link)
    for link in links:
        names = link.split('/')[-1]
        names = names.strip()
        name = names.replace('pm_data_hourly-', '')
        if (name != 'data_dictionary.csv') & (name not in exit_file_name):
            req = requests.get(link, verify=False)
            url_content = req.content
            file_p = data_folder + name
            csv_file = open(file_p, 'wb')
            csv_file.write(url_content)
            csv_file.close()


def _clean_df():
    if not os.path.exists(clean_folder):
        os.makedirs(clean_folder)
    column_names = ['station_id', 'name_th', 'name_en', 'area_th', 'area_en',
       'station_type', 'lat', 'long', 'date', 'time', 'pm25_color_id',
       'pm25_aqi', 'pm25_value', 'province', 'datetime']
    df_all = pd.DataFrame(columns=column_names)
    for name in os.listdir(data_folder):
        if name.endswith('.csv'):
            path = data_folder + name
            df = pd.read_csv(path)
            area_en = []
            for area in df['area_en']:
                area = area.strip().split(',')[-1].strip()
                area_en.append(area)
            df['province'] = area_en
            df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])
            df_all = pd.concat([df_all, df], axis=0, ignore_index=True)
            df_all.drop_duplicates(inplace=True)
            df_all.to_csv(clean_folder + '/all_data.csv')


with DAG(
    'etl',
    start_date = timezone.datetime(2024, 5, 3),
    schedule = '@hourly',
    tags = ['swu'],
) as dag:

    start = EmptyOperator(
        task_id = 'start',
        dag = dag,
    )

    empty = EmptyOperator(task_id='empty')

    get_files = PythonOperator(
        task_id = 'get_files',
        python_callable = _get_files,

    )

    gcs_path = 'pm25_raw/'
    bucket_name = 'swu-ds-525' # bucket name on GCS
    csv_files = [file for file in os.listdir(data_folder) if file.endswith('.csv')]
    path = []
    for csv_file in csv_files:
        path.append(data_folder + csv_file)

    upload_to_gcs = LocalFilesystemToGCSOperator(
        task_id = 'upload_to_gcs',
        src = path,
        dst = gcs_path,  # Destination file in the bucket
        bucket = bucket_name,  # Bucket name
        gcp_conn_id = 'my_gcp_conn',  # Google Cloud connection id
        mime_type = 'text/csv'
    )

    clean_df = PythonOperator(
        task_id = 'clean_df',
        python_callable = _clean_df,
    ) 

    upload_clean_to_gcs = LocalFilesystemToGCSOperator(
        task_id = 'upload_clean_to_gcs',
        src = [clean_folder + '/all_data.csv'],
        dst = 'pm25_cleaned/',
        bucket = bucket_name,
        gcp_conn_id = 'my_gcp_conn',
        mime_type = 'text/csv',
    )
    
    create_dataset = BigQueryCreateEmptyDatasetOperator(
        task_id = 'create_dataset',
        dataset_id = 'capstone_aqgs',
        gcp_conn_id = 'my_gcp_conn',
    )

    gcs_to_bq_pm25_trans = GCSToBigQueryOperator(
        task_id = 'gcs_to_bq_pm25_trans',
        bucket = bucket_name,
        source_objects = ['pm25_cleaned/all_data.csv'],
        destination_project_dataset_table = 'capstone_aqgs.pm25_transaction',
        create_disposition = 'CREATE_IF_NEEDED',
        write_disposition = 'WRITE_TRUNCATE',
        gcp_conn_id = 'my_gcp_conn',
    )

    manage_table_sql = f"""
        ALTER TABLE `capstone_aqgs.pm25_transaction`
        DROP COLUMN int64_field_0,
        ADD COLUMN pollutant STRING;


        UPDATE `capstone_aqgs.pm25_transaction`
        SET pollutant = 'pm25'
        WHERE pollutant IS null;


        CREATE OR REPLACE TABLE `capstone_aqgs.station`
        AS (
            SELECT 
                station_id, 
                name_th, name_en, 
                area_th, area_en, 
                province, 
                station_type, 
                lat, long
            FROM `capstone_aqgs.pm25_transaction`
            GROUP BY station_id, name_th, name_en, area_th, area_en, province, station_type, lat, long
        );


        CREATE OR REPLACE TABLE `capstone_aqgs.pm25_trans`
        PARTITION BY date
        AS (
            SELECT 
                station_id, 
                date, time, datetime, 
                pm25_color_id, 
                pm25_aqi, 
                pm25_value,
                pollutant
            FROM `capstone_aqgs.pm25_transaction`
            GROUP BY station_id, date, time, datetime, pm25_color_id, pm25_aqi, pm25_value, pollutant
        );

        DROP TABLE `capstone_aqgs.pm25_transaction`;


        CREATE OR REPLACE TABLE `capstone_aqgs.who_guidline` (
            pollutant STRING,
            avgtime STRING,
            aqgs INTEGER,
            date DATE
        );

        INSERT INTO `capstone_aqgs.who_guidline` (pollutant, avgtime, aqgs, date)
        VALUES ('pm25', '24-hour', 5, '2021-01-01'),
               ('pm25', 'Annual', 15, '2021-01-01'),
               ('pm25', '24-hour',10, '2005-01-01'),
               ('pm25', 'Annual', 25, '2005-01-01');
    """

    manage_table = BigQueryExecuteQueryOperator(
        task_id='manage_table',
        sql=manage_table_sql,
        use_legacy_sql=False,
        gcp_conn_id='my_gcp_conn',
    )

    end = EmptyOperator(task_id = 'end')

    start >> get_files >> [upload_to_gcs, clean_df] >> empty >> [upload_clean_to_gcs, create_dataset] >> gcs_to_bq_pm25_trans >> manage_table >> end