from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

from spiders.fl.crawler import FLSpider
from spiders.utils import start_crawl

with DAG(
    dag_id="fl",
    schedule="*/1 * * * *",
    start_date=days_ago(1),
    catchup=False,
):
    t1 = PythonOperator(
        task_id=f"fl",
        python_callable=start_crawl,
        op_kwargs={
            "crawler": FLSpider
        },
    )

    chain(t1)
