"""This module parse urls and save data to GoogleSheets"""
import logging
from random import choice
from datetime import datetime, timedelta

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

month_names = {
    'января': 1,
    'февраля': 2,
    'марта': 3,
    'апреля': 4,
    'мая': 5,
    'июня': 6,
    'июля': 7,
    'августа': 8,
    'сентября': 9,
    'октября': 10,
    'ноября': 11,
    'декабря': 12
}

"""Парсинг полученного url  и запись в таблицу"""
def parse(url):
    response = session.get(url, timeout=5)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')
        records_list = []
        records = soup.find_all("div", "list__item columns small-12")
        for record in records:
            title = record.find("h6")
            link = "https://msp29.ru" + title.find('a').get('href')

            date_string = record.find("div", "table__td").text
            day, month_name, year = date_string.split()
            month = month_names[month_name]
            date_tmp = datetime(int(year), month, int(day))
            date = date_tmp.strftime("%d.%m.%Y")
            records_list.append({'title': title.text.strip(),
                                'link': link, 'date': date})
        # Записываем данные в Google Sheets
        for record in records_list:
            row = [record['title'], record['link'], record['date'], url]
            sheet.append_row(row)
    else:
        print("Error")
