import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from config import GOOGLE_SHEET_NAME

def connect_to_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_credentials.json", scope)
    client = gspread.authorize(creds)
    try:
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    except gspread.SpreadsheetNotFound:
        sheet = client.create(GOOGLE_SHEET_NAME).sheet1
        sheet.append_row(["Дата", "Username", "Состав заказа", "Адрес", "Сумма", "Статус оплаты"])
    return sheet

def add_order(sheet, username, items, address, total, status):
    row = [datetime.now().strftime("%Y-%m-%d %H:%M"), username, items, address, total, status]
    sheet.append_row(row)
