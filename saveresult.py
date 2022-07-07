
import os
import csv

from googe_sheet_api import GoogleSheet

from openpyxl import Workbook
from openpyxl.styles import Font

import config

def read_csvs():
    # читает отклики из всех csv файлов в один массив
    data = []
    data.append(["ВЫКАНСИЯ", "ДАТА", "ФИО", "ПОЛ", "ВОЗРАСТ", "ТЕЛЕФОН",
        "EMAIL", "МЕСТОПОЛОЖЕНИЕ", "МОБИЛЬНОСТЬ", "ДОЛЖНОСТЬ", "ЗАРПЛАТА",
        "ПОСЛЕДНЕЕ МЕСТО РАБОТЫ", "ПОСЛЕДНЯЯ ДОЛЖНОСТЬ", "ОПЫТ ВОЖДЕНИЯ",
        "ПИСЬМО", "URL ОТКЛИКА", "URL ВАКАНСИИ"])
    content = os.listdir('Out')
    for file_name in content:
        if "resumeId=" in file_name:        # если имя файла содержит resumeId= - файл с откликом
            with open(f"Out\\{file_name}", encoding="utf8") as f:
                reader = csv.reader(f)
                for row in reader:
                    row[5] = row[5].replace("+", "")    # в телефоне убираем + иначе в гугле пишет ошибку
                    data.append(row)
    return data

def csvs_to_excel():
    # сохраняем данные в excel
    excel_file = Workbook()
    excel_sheet = excel_file.create_sheet(title="Data", index=0)

    list(map(lambda x: excel_sheet.append(x), read_csvs()))

    excel_sheet.row_dimensions[1].font = Font(bold=True)
    excel_sheet.column_dimensions["A"].font = Font(bold=True)
    excel_sheet.freeze_panes = "A2"

    excel_file.save(filename=config.cnf["Result"]["excel_file_neme"])


def csvs_to_sheet():
    # сохраняем данные в googl
#    print(config.cnf["Result"]["google_sheet_id"])
    gs = GoogleSheet(config.cnf["Result"]["google_sheet_id"])
    g_range = "Лист1!A1:Z"
    gs.clearSheet(g_range)

    g_result = read_csvs()
    g_range = f"Лист1!A1:Q{len(g_result)+1}"
    gs.updateRangeValues(g_range, g_result)


def save_result():
    # сохраняем данные в зависимости от конфига
    if config.cnf["Result"]["save_to"] in 'google':
        csvs_to_sheet()
    else:
        csvs_to_excel()

def resave():
    content = os.listdir('Out')
    for file_name in content:
        if "resumeId=" in file_name:        # если имя файла содержит resumeId= - файл с откликом
            with open(f"Out\\{file_name}", encoding="utf8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row[5]) > 0 or len(row[6]) > 0:
                        with open(f"Out2\\{file_name}", "w", newline="", encoding="utf8") as f:
                            writer = csv.writer(f)
                            writer.writerows([row])


def clear_bad():
    content = os.listdir('Out')
    for file_name in content:
        if "resumeId=" in file_name:        # если имя файла содержит resumeId= - файл с откликом
            with open(f"Out\\{file_name}", encoding="utf8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row[5]) == 0 and len(row[6]) == 0:
                        # удаляем без контактоа
                        os.remove(f"Out\\{file_name}")
                        print("del")



if __name__ == '__main__':
    config.cnf.read("config.ini")
    save_result()
#    resave()