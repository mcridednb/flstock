# freelance-crawler

### Новый паук:
```bash
cd airflow
scrapy genspider example example.com
```

### Airflow
#### Первичная настройка
```bash
export AIRFLOW_HOME=/Users/nikolaj/projects/freelance/crawlers/parser
airflow db init
mkdir -p ./parser/dags
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres_airflow/airflow_db
```

#### Что-то ещё
```bash
airflow db init

airflow db migrate

airflow users create \
    --username airflow \
    --firstname Nikolai \
    --lastname Admin \
    --role Admin \
    --email mcridednb@gmail.com

airflow webserver --port 8080

airflow scheduler
```# flstock
