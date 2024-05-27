from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

from spiders.habr.crawler import HabrSpider
from spiders.utils import start_crawl

with DAG(
    dag_id="habr",
    schedule="*/2 * * * *",
    start_date=days_ago(1),
    catchup=False,
):
    t1 = PythonOperator(
        task_id=f"habr",
        python_callable=start_crawl,
        op_kwargs={
            "crawler": HabrSpider
        },
    )

    chain(t1)
