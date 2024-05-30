from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

from spiders.freelance.crawler import FreelanceSpider
from spiders.utils import start_crawl

with DAG(
    dag_id="freelance",
    schedule="*/2 * * * *",
    start_date=days_ago(1),
    catchup=False,
):
    t1 = PythonOperator(
        task_id=f"freelance",
        python_callable=start_crawl,
        op_kwargs={
            "crawler": FreelanceSpider
        },
    )

    chain(t1)
