import bz2
import os
import pickle

from airflow.models.xcom import BaseXCom
import pandas as pd
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)


class RedisXComBackend(BaseXCom):
    PREFIX = "xcom-data"

    @staticmethod
    def create_redis_key(task_id):
        return f"{RedisXComBackend.PREFIX}:{task_id}"

    @staticmethod
    def serialize_value(
        value,
        key=None,
        task_id=None,
        dag_id=None,
        run_id=None,
        map_index=None,
        **kwargs
    ):
        with redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0) as r:
            if isinstance(value, pd.DataFrame):
                pickled_df = bz2.compress(pickle.dumps(value))
                result = RedisXComBackend.create_redis_key(task_id)
                r.set(result, pickled_df)
            else:
                result = value
            return BaseXCom.serialize_value(value=result)

    @staticmethod
    def deserialize_value(result):
        result = BaseXCom.deserialize_value(result)
        with redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0) as r:
            redis_data = r.get(result)

            if not redis_data:
                return result
            else:
                data = pickle.loads(bz2.decompress(redis_data))
                r.delete(result)
                return data
