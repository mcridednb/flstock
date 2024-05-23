from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

from spiders.kwork.crawler import KworkSpider
from spiders.utils import start_crawl

with DAG(
    dag_id="kwork",
    schedule="*/1 * * * *",
    start_date=days_ago(1),
    catchup=False,
):
    t1 = PythonOperator(
        task_id=f"kwork",
        python_callable=start_crawl,
        op_kwargs={
            "crawler": KworkSpider
        },
    )

    chain(t1)
