from airflow.models import DAG
from typing import NoReturn
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
import logging
import pickle
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import requests
import os
from dotenv import load_dotenv

load_dotenv() 

#Сформируем интервал запуска ежедневно в 16:30 по UTC
dag = DAG('PARSER',
          schedule_interval="30 16 * * *",
          start_date=days_ago(2),
          catchup=False,
          tags=["Big_data"]
          )

api_token = os.getenv('AVIASALES_API_TOKEN')


_LOG = logging.getLogger()
_LOG.addHandler(logging.StreamHandler())


def init() -> NoReturn:
    _LOG.info('Parsing started')


#Функция обращения к API 
def get_price(origin, destination):
    response = requests.get("http://api.travelpayouts.com/aviasales/v3/get_latest_prices",
                            params = {'origin': origin,
                                      'destination' : destination,
                                      'one_way':True,
                                      'period_type':'year',
                                      'limit': '999',
                                      'sorting': 'price',
                                      'token':api_token})
    if not response.ok:
        print('Server responded:', response.status_code)
    else:
        resp = response.json()
    return resp


#Получение цены по направлению
def cheap(origin):
    cities = ['KJA', 'MOW', 'LED', 'BAX', 'ASF', 'KZN', 'KGD', 'ABA', 
              'VOZ', 'UUS', 'SVX', 'KRR', 'AYT', 'VIE', 'DXB']
    
    # Фильтруем города, исключая город отправления
    target_cities = [city for city in cities if city != origin]
    
    dep_cities = []
    
    for city in target_cities:
        price = get_price(origin, city)
        dep_cities.append(price)
        
    return dep_cities



BUCKET = 'mlds-de'
DATA_PATH = 'datasets/data_1.pkl'

#Загрузка данных на S3
def parsing_s():
    airport_codes = ['MOW', 'KJA', 'LED', 'BAX', 'ASF', 'KZN', 'KGD', 
                     'ABA', 'VOZ', 'UUS', 'SVX', 'KRR', 'AYT', 'VIE', 'DXB']

    # Собираем данные для каждого кода аэропорта
    data = []
    for code in airport_codes:
        data.extend(cheap(code))

    # Сохраняем данные в S3
    s3_hook = S3Hook('s3_cn')
    session = s3_hook.get_session('ru-central1')
    resource = session.resource('s3')

    pickle_save = pickle.dumps(data)
    resource.Object(BUCKET, DATA_PATH).put(Body=pickle_save)



task_init = PythonOperator(task_id='init', python_callable=init, dag=dag)

task_parsing_s = PythonOperator(task_id='parsing_s', python_callable=parsing_s, dag=dag)

task_init >> task_parsing_s