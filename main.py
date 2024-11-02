from collections import deque
import boto3
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

load_dotenv() 

def print_hi(name):
    print(f'Hi, {name}')

if __name__ == '__main__':
    print_hi('streamlit')


st.title("CHEAP FLIGHTS")
st.write("")

# UI  Streamlit

date = '2024-01-22'

# Создаем DataFrame с городами и кодами IATA
directions = pd.DataFrame({
    'Cities': ['Moscow', 'Krasnoyarsk', 'Saint Petersburg',
               'Barnaul', 'Astrakhan', 'Kazan', 'Kaliningrad',
               'Abakan', 'Voronezh', 'Yuzhno-Sakhalinsk',
               'Ekaterinburg', 'Krasnodar', 'Antalya',
               'Vienna', 'Dubai'],
    'IATA': ['MOW', 'KJA', 'LED', 'BAX', 'ASF', 'KZN', 'KGD', 'ABA', 'VOZ', 'UUS', 'SVX', 'KRR', 'AYT', 'VIE', 'DXB']
})

city_to_iata = dict(zip(directions['Cities'], directions['IATA']))
iata_to_city = dict(zip(directions['IATA'], directions['Cities']))

cities = directions['Cities']

dep = st.selectbox('Выберите город отправления', cities)
st.write('Ваш город вылета:', dep)
dep = city_to_iata[dep]
st.write(dep)

arr = st.selectbox('Выберите город прибытия', cities)
st.write('Ваш город прибытия:', arr)
arr = city_to_iata[arr]
st.write(arr)


date = st.text_input('Напишите дату вылета (YYYY-MM-DD):')
st.write('Дата вылета:', date)

#Получение данных из хранилища

S3_CREDS = {
    "aws_access_key_id": os.environ['AWS_ACCESS_KEY_ID'],
    "aws_secret_access_key":os.environ['AWS_SECRET_ACCESS_KEY']
}


bucket_name = "mlds-de"
data_path = 'datasets/data_1.pkl'


s3r = boto3.resource(service_name='s3', endpoint_url='https://storage.yandexcloud.net', **S3_CREDS)
bucket = s3r.Bucket(bucket_name)



bucket.download_file('datasets/data_1.pkl', bucket_name)


list_c = pd.read_pickle('mlds-de')


#Реализуем функцию add_edge для заполнения нашего графа.


def add_edge(G, a, b, weight):
    if a not in G:
        G[a] = {b:weight}
    else:
        G[a][b] = weight



def dijkstra_path(G, start, end):
    result = ''
    Q = deque()  # Q представляем как очередь
    s = {}  # словарь расстояний графа
    p = {start: None}  # список "родителей" вершин
    s[start] = 0
    Q.append(start)
    while Q:  # пока очередь не пуста
        v = Q.pop()  # достаем элемент (вершину) из очереди
        for u in G[v]:  # проходимся циклом по его соседям
            if u not in s or s[v] + G[v][u] < s[u]:  # если вершина не в очереди или новое расстояние до нее меньше, чем изначальное
                s[u] = s[v] + G[v][u]  # фиксируем это расстояние
                p[u] = v  # фиксируем "родителя" в соответствующий список "вершин"
                Q.append(u)  # добавляем соседей вершины в очередь для обработки

    # Ниже реализуем фиксацию пути обхода графа по кратчайшему расстоянию
    path = [end]
    parent = p[end]
    while not parent is None:
        path.append(parent)
        parent = p[parent]
    print('Air route: ', end='')
    for i in path[::-1]:
        if i != path[0]:
            result += iata_to_city[i] + ' -> '
            print(iata_to_city[i], '-> ', end='')
        else:
            result += iata_to_city[i]
            print(iata_to_city[i])

    for k in s:
        if k == end:
            print('Price:', s[end])
            result += '\n | Цена в RUB: ' + str(s[end])

    st.write('Наиболее дешевый маршрут:', result)





a = [] # задается список вершин графа, где ими будут выступать пункты вылета/прилета
b = [] # задается список вершин графа, где ими будут выступать пункты вылета/прилета
weight = [] # в данном списке будут хранится веса между вершинами(ребрами)
for i in range(len(list_c)):
    for k in range(len(list_c[i]['data'])): #поиск циклом внутри списка маршрутов с нужной датой и добавляется в соотв. список
        if date == list_c[i]['data'][k]['depart_date'].split('T')[0]:
            a.append(list_c[i]['data'][k]['origin'])
            b.append(list_c[i]['data'][k]['destination'])
            weight.append(list_c[i]['data'][k]['value'])


G = {}
for i, j, k in zip(a, b, weight):
    add_edge(G, i, j, k)
    add_edge(G, j, i, k)

m = dijkstra_path(G,dep, arr)

print(m)



#Соберем датафрейм из данных по городу вылета

unity_df = pd.DataFrame()
for i in range(len(list_c)):
    df = pd.DataFrame(list_c[i]['data'])
    unity_df = pd.concat([unity_df,df], axis=0, ignore_index=True)




df_dep_city = unity_df[unity_df['origin'] == dep]

df_dep_city['depart_date'] = pd.to_datetime(df_dep_city['depart_date'])

df_grp = df_dep_city.groupby(df_dep_city['depart_date'].dt.month)['value'].mean().reset_index()

fig, ax = plt.subplots()
ax.plot(df_grp['depart_date'], df_grp['value'], marker='o', linestyle='-', color='r')
ax.set_xlabel('Месяц')
ax.set_ylabel('Стоимость билета, RUB')
ax.set_title('Динамика стоимости билетов в 2024 году из ' + iata_to_city[dep])
ax.grid(True)
st.pyplot(fig)
