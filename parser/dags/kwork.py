from datetime import datetime

from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.python import PythonOperator

from spiders.kwork.crawler import KworkSpider
from spiders.utils import start_crawl

start_date = datetime.today().now()

with DAG(
    dag_id="kwork",
    schedule="*/5 * * * *",
    start_date=start_date,
):
    t1 = PythonOperator(
        task_id=f"kwork",
        python_callable=start_crawl,
        op_kwargs={
            "crawler": KworkSpider
        },
    )

    chain(t1)
