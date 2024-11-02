# Сервис по поиску дешевых авиаперелетов с использованием алгоритма Дейкстры

Этот проект представляет собой веб-сервис на базе Streamlit, который позволяет пользователю находить наиболее дешевые авиаперелеты между заданными городами, используя данные о ценах из API Aviasales.

### Логика работы сервиса

1. **Ежедневная загрузка данных с помощью DAG-скрипта в Airflow**  
   DAG-скрипт в Airflow ежедневно загружает актуальные данные о ценах на перелеты из API Aviasales в облачное хранилище S3. Для каждого города из списка ниже записываются данные о возможных маршрутах и ценах:
   - Красноярск, Москва, Санкт-Петербург, Барнаул, Астрахань, Казань, Калининград, Абакан, Воронеж, Южно-Сахалинск, Екатеринбург, Краснодар, Анталья, Вена, Дубай.

2. **Построение графа маршрутов с весами на основе данных S3**  
   При запуске сервиса Streamlit загружает данные из S3. Пользователь выбирает пункт отправления и назначения, после чего строится взвешенный граф с узлами (городами) и ребрами (маршрутами между ними), где вес каждого ребра — это стоимость перелета. Алгоритм Дейкстры используется для поиска самого дешевого маршрута между указанными пользователем городами.  
   Визуализация графа:  
   ![Граф](cheap_flights/Graph.png)

3. **Отображение результата пользователю**  
   Пользователь получает наиболее дешёвый маршрут между городами, выбранными из списка. Также сервис отображает график со среднемесячными ценами на перелеты из города отправления по всем доступным направлениям.  
   Пример работы сервиса:  
   ![Работа сервиса](cheap_flights/service_working.png)

### Стек технологий

- **Python 3.11**: для основной логики сервиса и разработки алгоритмов.
- **Apache Airflow**: для автоматизации ежедневной загрузки данных о ценах.
- **Yandex Cloud S3**: для хранения данных о ценах на перелеты.
- **Streamlit**: для создания интерактивного веб-интерфейса, доступного пользователям.