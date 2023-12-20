import datetime

import requests
import json
import os
import sqlite3

token = '1567153043b92ef2b4e43f88db0fdb99f760653e'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

def time():
    date = datetime.datetime.now()
    dayWeek = date.weekday()
    # Если понедельник
    if dayWeek == 0:
        start =  date - datetime.timedelta(days=2)
        end = date - datetime.timedelta(days=1)
    elif dayWeek == 6:
        return None
    else:
        start = date - datetime.timedelta(days=1)

def getData():
    # Розничные продажи
    url = f"https://api.moysklad.ru/api/remap/1.2/entity/retaildemand"
    response = requests.get(url = url,headers=headers)
    result = response.json()
    with open("sales.json", "w") as write_file:
        write_file.write(json.dumps(result, indent=4))
    # Список товаров
    url = 'https://api.moysklad.ru/api/remap/1.2/entity/product'
    response = requests.get(url = url,headers=headers)
    result = response.json()
    with open("product.json", "w") as write_file:
        write_file.write(json.dumps(result, indent=4))
    # Розничные возвраты
    url = 'https://api.moysklad.ru/api/remap/1.2/entity/retailsalesreturn'
    response = requests.get(url=url, headers=headers)
    result = response.json()
    with open("return.json", "w") as write_file:
        write_file.write(json.dumps(result, indent=4))
    url = 'https://api.moysklad.ru/api/remap/1.2/entity/retailstore'
    response = requests.get(url=url, headers=headers)
    result = response.json()
    with open("store.json", "w") as write_file:
        write_file.write(json.dumps(result, indent=4))

    url = 'https://api.moysklad.ru/api/remap/1.2/report/stock/all/current'
    response = requests.get(url=url, headers=headers)
    result = response.json()
    with open("stockCount.json", "w") as write_file:
        write_file.write(json.dumps(result, indent=4))

def createDb():
    connection = sqlite3.connect('moysklad.db')
    cursor = connection.cursor()
    # Создание БД
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS retailStore (
        retailStore_id TEXT PRIMARY KEY,
        name TEXT NOT NULL
        );''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product (
        product_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        cost TEXT NOT NULL,
        countinstock INTEGER NOT NULL
        );''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS demands (
        demands_id TEXT PRIMARY KEY,
        product_id TEXT NOT NULL,
        count INTEGER NOT NULL,
        retailstore_id TEXT NOT NULL,
        datetime TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES product (id),
        FOREIGN KEY (retailstore_id) REFERENCES retailStore (id)
        );''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS returns (
        returns_id TEXT PRIMARY KEY,
        product_id TEXT NOT NULL,
        count INTEGER NOT NULL,
        retailstore_id TEXT NOT NULL,
        datetime TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES product (id),
        FOREIGN KEY (retailstore_id) REFERENCES retailStore (id)
        );''')

    connection.commit()
    connection.close()

def insertDate():
    connection = sqlite3.connect('moysklad.db')
    cursor = connection.cursor()
    # Внесение точек продаж
    with open("store.json", "r") as read_file:
        data = json.load(read_file)
    for item in data['rows']:
        cursor.execute('INSERT INTO retailStore (retailStore_id, name) VALUES (?, ?)', (item["id"], item["name"]))
    # Внесение товаров
    with open('product.json', 'r') as read_file:
        data = json.load((read_file))
    with open('stockCount.json', 'r') as read_file:
        data1 = json.load((read_file))
    for item in data['rows']:
        for item1 in data1:
            if item1['assortmentId'] == item['id']:
                cursor.execute('INSERT INTO product (product_id, name, cost , countinstock) VALUES (?, ?, ?, ?)', (item['id'], item['name'], item['salePrices'][0]['value'] , item1['stock']))
    # Продажи
    with open('sales.json', 'r') as read_file:
        data = json.load(read_file)
        for item in data['rows']:
            response = requests.get(item["positions"]["meta"]["href"], headers=headers)
            result = response.json()
            count = result['rows'][0]['quantity']

            response = requests.get(result['rows'][0]["assortment"]["meta"]["href"], headers=headers)
            result = response.json()
            product_id = result["id"]

            response = requests.get(item['retailStore']['meta']['href'], headers=headers)
            result = response.json()
            retailStoreId = result['id']
            cursor.execute(
                'INSERT INTO demands (demands_id, product_id, count, retailstore_id, datetime) VALUES (?, ?, ?, ?, ?)',
                (item['id'], product_id, count, retailStoreId, item['moment']))
    # Возвраты
    with open('return.json', 'r') as read_file:
        data = json.load(read_file)
        for item in data['rows']:
            response = requests.get(item["positions"]["meta"]["href"], headers=headers)
            result = response.json()
            count = result['rows'][0]['quantity']

            response = requests.get(result['rows'][0]["assortment"]["meta"]["href"], headers=headers)
            result = response.json()
            product_id = result["id"]

            response = requests.get(item['retailStore']['meta']['href'], headers=headers)
            result = response.json()
            retailStoreId = result['id']
            cursor.execute(
                'INSERT INTO returns (returns_id, product_id, count, retailstore_id, datetime) VALUES (?, ?, ?, ?, ?)',
                (item['id'], product_id, count, retailStoreId, item['moment']))
    connection.commit()
    connection.close()
#createDb()
#insertDate()



def workData():
    conn = sqlite3.connect('moysklad.db')
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM demands WHERE datetime = 2023-12-18", )
    rows = cursor.fetchall()
    print(rows)

# Форма создания внутреннего заказа
def post():
    url = 'https://api.moysklad.ru/api/remap/1.2/entity/internalorder'
    data = {
        'name': '123',
        'description': '1233',
        'organization': {
        'meta': {
                'href': 'https://api.moysklad.ru/api/remap/1.2/entity/organization/49913266-99f5-11ee-0a80-0f680001dff7',
            "type": "organization"
            }
        },
        'agent': {
            'meta': {
                'href': 'https://api.moysklad.ru/api/remap/1.2/entity/organization/49913266-99f5-11ee-0a80-0f680001dff7'
            }
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    print(response.status_code)
    print(response.text)

#getData()
#createDb()
#insertDate()
#workData()