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
        records = soup.find_all("div", "row mb-3")
        for record in records:
            title = record.find("div", "col-10")
            link = record.find("a", "btn btn-primary").get('href')
            date_string = title.find("strong", "m-l-5").text.strip()
            records_list.append({'title': title.text.strip(), 'link': link, 'date': date_string})
            date_diff = datetime.strptime(date_string, "%d.%m.%Y").date()
            difference = today - date_diff
            if difference > timedelta(days=30):
                break
        # Записываем данные в Google Sheets
        for record in records_list:
            time.sleep(1)
            row = [record['title'], record['link'], record['date'], response.url]
            sheet.append_row(row)
    else:
        print("Error status_code =", response.status_code)

        