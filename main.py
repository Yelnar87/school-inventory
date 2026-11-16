import gspread
import pandas as pd

# Подключение к Google Таблице (требуется файл ключа доступа service_account.json от Google Cloud)
# Инструкцию по получению json-ключа можно найти в документации gspread
def get_sheet_data():
    gc = gspread.service_account(filename='service_account.json')
    sh = gc.open("Школьный учет оборудования")
    worksheet = sh.worksheet("Inventory")
    return pd.DataFrame(worksheet.get_all_records())

if __name__ == "__main__":
    df = get_sheet_data()
    print("Данные из облака успешно загружены:")
    print(df)