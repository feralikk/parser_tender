"""This module parse urls and save data to GoogleSheets"""
import logging
from datetime import datetime, timedelta
from random import choice
import time

import requests
import gspread

from oauth2client.service_account import ServiceAccountCredentials
from bs4 import BeautifulSoup

logging.basicConfig(filename="parser.log", level=logging.ERROR,
                    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger()

# Подключение к Google Sheets
CREDENTIALS_FILE = 'creds.json'
SPREADSHEET_ID = ''
# Авторизуемся и получаем service — экземпляр доступа к API
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
client = gspread.authorize(credentials)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# Добавляем заголовки в первую строку листа
header = ['Title', 'Link', 'Date', 'Source']
sheet.append_row(header)

# Список с заголовками для http-запроса
DESKTOP_AGENTS = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',)

# Вызов рандомого заголовка для http-запроса
session = requests.Session()
session.headers = {'User-Agent': choice(DESKTOP_AGENTS),
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}

today = datetime.now().date()


def parse(url):
    response = session.get(url, timeout=5)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')
        records_list = []
        # Находим тег <div class="konkTitle">Закрытие</div>
        konktitle_tag = soup.find('div', class_='konkTitle', text='Закрытые:')
        # Находим все теги <div class="konkOtk">, которые находятся перед тегом <div class="konkTitle">Закрытие</div>
        all_konkotk_tags_before_konktitle = konktitle_tag.find_all_previous('div', class_='konkOtk')
        for record in reversed(all_konkotk_tags_before_konktitle):
            title = record.find("div", "konkoTitle").text.strip()
            link = "http://ncpp.ru" + record.find("a").get('href')
            records_list.append({'title': title, 'link': link, 'date': ""})
        # Записываем данные в Google Sheets
        for record in records_list:
            time.sleep(1)
            row = [record['title'], record['link'], record['date'], response.url]
            sheet.append_row(row)
    else:
        print("Error status_code =", response.status_code)
        