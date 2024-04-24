from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.utils import timezone

import logging

def _get_dog_api():
    response = requests.get("")
    data = respones.json()
    logging.info(data)
    with

with DAG(
    "hello",
    start_date=timezone.datetime(2024, 3, 23),
    schedule=None,
    tags=["DS525"],
):
    start = EmptyOperator(task_id="start")

    get_dog_api = PythonOperator(
        task_id="get_dog_api",
        python_callable=_get_dog_api,
    )

    end = EmptyOperator(task_id="end")

    start >> echo_hello >> end
    start >> say_hello >> end

# with open("hello.txt","w") as f:
#     fdsfdslj
#     fdsfdslj

# f = open("")
# f.close()

# print("Hello")