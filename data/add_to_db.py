import json
import sqlite3

# Подключение к базе данных SQLite
conn = sqlite3.connect('C:/Dev/sprint18/foodgram/backend/foodgram/db.sqlite3')
cursor = conn.cursor()

# Создание таблицы, если она еще не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS recipes_ingredient (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    measurement_unit TEXT NOT NULL
)
''')

# Загрузка данных из JSON-файла
with open('C:/Dev/sprint18/foodgram/data/ingredients.json', 'r',
          encoding='utf-8') as file:
    data = json.load(file)

# Вставка данных в таблицу
for item in data:
    cursor.execute('''
    INSERT INTO recipes_ingredient (name, measurement_unit)
    VALUES (?, ?)
    ''', (item['name'], item['measurement_unit']))

# Сохранение изменений и закрытие соединения
conn.commit()
conn.close()

print("Данные успешно добавлены в таблицу recipes_ingredient.")
