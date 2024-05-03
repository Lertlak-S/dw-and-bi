import json
import glob
import os
import requests
import logging

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from airflow.providers.google.cloud.transfers.local_to_gcs import LocalFilesystemToGCSOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateEmptyDatasetOperator
# from airflow.contrib.operators.bigquery_operator import BigQueryOperator
# from airflow.providers.google.cloud.operators.bigquery import BigQueryOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryExecuteQueryOperator
# from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
# from airflow.providers.postgres.hooks.postgres import PostgresHook
from bs4 import BeautifulSoup 
from airflow.utils import timezone
from datetime import datetime
from typing import List


# def _get_files(filepath):
#     """
#     Description: This function is responsible for listing the files in a directory
#     """

#     all_files = []
#     for root, dirs, files in os.walk(filepath):
#         files = glob.glob(os.path.join(root, "*.csv"))
#         for f in files:
#             all_files.append(os.path.abspath(f))

#     num_files = len(all_files)
#     print(f"{num_files} files found in {filepath}")

#     return all_files


def _get_files():
    url = "https://opendata.onde.go.th/dataset/14-pm-25"
    links = []
    req = requests.get(url, verify=False)
    req.encoding = "utf-8"
    soup = BeautifulSoup(req.text, 'html.parser')
    #print(soup.prettify())
    og = soup.find("meta",  property="og:url")
    base = urlparse(url)
    for link in soup.find_all('a'):
        current_link = link.get('href')
        if str(current_link).endswith('csv'):
            links.append(current_link)
    for link in links:
        names = link.split("/")[-1]
        names = names.strip()
        name = names.replace("pm_data_hourly-","")
        if name != "data_dictionary.csv":
            req = requests.get(link, verify=False)
            url_content = req.content
            file_p = "/opt/airflow/dags/data/" + name
            csv_file = open(file_p, "wb")
            csv_file.write(url_content)
            csv_file.close()


with DAG(
    "etl",
    start_date=timezone.datetime(2024, 5, 3),
    schedule="@daily",
    tags=["swu"],
) as dag:

    start = EmptyOperator(
        task_id="start",
        dag=dag,
    )

    empty = EmptyOperator(task_id="empty")

    get_files = PythonOperator(
        task_id="get_files",
        python_callable=_get_files,
        # op_kwargs={
        #     "filepath":"/opt/airflow/dags/data",
        # },
    )

    data_folder = "/opt/airflow/dags/data/" # local dir
    gcs_path = "pm25/"
    bucket_name = "swu-ds-525" # bucket name on GCS
    csv_files = [file for file in os.listdir(data_folder) if file.endswith(".csv")]
    path = []
    for csv_file in csv_files:
        path.append(data_folder + csv_file)

    upload_file_gcs = LocalFilesystemToGCSOperator(
        task_id='upload_file_gcs',
        src=path,
        dst=gcs_path,  # Destination file in the bucket
        bucket=bucket_name,  # Bucket name
        gcp_conn_id='my_gcp_conn',  # Google Cloud connection id
        mime_type='text/csv'
    )

    create_dataset = BigQueryCreateEmptyDatasetOperator(
        task_id='create_dataset',
        dataset_id='capstone_aqgs',
        gcp_conn_id='my_gcp_conn',
    )

    gcs_to_bq_pm25_trans = GCSToBigQueryOperator(
        task_id='gcs_to_bq_pm25_trans',
        bucket=bucket_name,
        source_objects=['pm25/*.csv'],
        destination_project_dataset_table='capstone_aqgs.pm25_trans',
        create_disposition='CREATE_IF_NEEDED',
        write_disposition='WRITE_TRUNCATE',
        gcp_conn_id='my_gcp_conn',
    )

    gcs_to_bq_station = GCSToBigQueryOperator(
        task_id='gcs_to_bq_station',
        bucket=bucket_name,
        source_objects=['pm25/*.csv'],
        destination_project_dataset_table='capstone_aqgs.station',
        schema_fields=[
            {'name': 'station_id'  , 'type': 'STRING'},
            {'name': 'name_th'     , 'type': 'STRING'},
            {'name': 'name_en'     , 'type': 'STRING'},
            {'name': 'area_th'     , 'type': 'STRING'},
            {'name': 'area_en'     , 'type': 'STRING'},
            {'name': 'station_type', 'type': 'STRING'},
            {'name': 'lat'         , 'type': 'FLOAT'},
            {'name': 'long'        , 'type': 'FLOAT'},
        ],
        create_disposition='CREATE_IF_NEEDED',
        write_disposition='WRITE_TRUNCATE',
        gcp_conn_id='my_gcp_conn',
        skip_leading_rows=1,
    )

    manage_table_sql = f"""
        ALTER TABLE `capstone_aqgs.pm25_trans`
        DROP COLUMN name_th,
        DROP COLUMN name_en,
        DROP COLUMN area_th,
        DROP COLUMN area_en,
        DROP COLUMN station_type,
        DROP COLUMN lat,
        DROP COLUMN long,
        
        ADD COLUMN pollutant STRING;

        UPDATE `capstone_aqgs.pm25_trans`
        SET pollutant = 'pm25'
        WHERE pollutant IS null;
    """

    manage_table = BigQueryExecuteQueryOperator(
        task_id='manage_table',
        sql=manage_table_sql,
        use_legacy_sql=False,
        gcp_conn_id='my_gcp_conn',
    )

    end = EmptyOperator(task_id="end")

    start >> get_files >> [upload_file_gcs, create_dataset] >> empty >> [gcs_to_bq_pm25_trans, gcs_to_bq_station] >> manage_table >> end