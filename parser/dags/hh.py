from airflow import DAG
from airflow.models.baseoperator import chain
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

from spiders.hh.crawler import HHSpider
from spiders.utils import start_crawl

with DAG(
    dag_id="hh",
    schedule="*/1 * * * *",
    start_date=days_ago(1),
    catchup=False,
):
    t1 = PythonOperator(
        task_id=f"hh",
        python_callable=start_crawl,
        op_kwargs={
            "crawler": HHSpider,
            "keyword": "python",
        },
    )
    t2 = PythonOperator(
        task_id=f"hh",
        python_callable=start_crawl,
        op_kwargs={
            "crawler": HHSpider,
            "keyword": "django",
        },
    )

    chain(t1, t2)
