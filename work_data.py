import os
import json

data_file = 'data.json'

def load_data():
    """
    Функция для загрузки данных из JSON
    :return:
    """
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_data(data):
    """ Функция для сохранения данных в JSON"""
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=4)
