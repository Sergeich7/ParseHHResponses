"""

ЛОГИКА РАБОТЫ

заходит на хх, авторизуется
находит живые вакансии и сохраняет в файл urls_vacs.csv
для каждой вакансии находит ссылки на резюме и сохраняет все в файл urls_resps.csv
если резюме не было разобрано (отсутствует файл resumeId=184917534.csv) - разбирает и сохраняет в файл resumeId=184917534.csv (те обрабатываются только новые отклики).
если все новые резюме разобрали, удаляем устаревшие resumeId= и urls_vacs.csv и urls_resps.csv
если вакансия перестала существовать, то отклики удаляются или остаются в базе (в зависимости от настроек в файле config.ini)
сохраняет результаты в файл excel или google sheet (в зависимости от настроек в файле config.ini)

Последние изменение: 07.07.2022


"""

import os
import time
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

from bs4 import BeautifulSoup as bs

from saveresult import save_result

import config
config.cnf.read("config.ini")

vacancies = []
urls_to_resume = []

def grab_hh():
    print("*** Старт")
    # Запускаем драйвер
    options = webdriver.ChromeOptions()
    if config.cnf["Chrome"]["hide_chrome"] == "True":
        # скрываем хром если мешает
        options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument(r"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36")
    services = Service('chromedriver.exe')
    driver = webdriver.Chrome(options=options, service=services)
    driver.implicitly_wait(int(config.cnf["Chrome"]["min_wait"]))
    wait_el = WebDriverWait(driver, int(config.cnf["Chrome"]["min_wait"]))
    driver.set_page_load_timeout(10)
    # переходим на сайт
    try:
        driver.get("https://hh.ru/employer/vacancies")
    except:
        pass
    # открываем пароль
    xpath_login_btn = "//button[@data-qa='expand-login-by-password']"
    wait_el.until(EC.visibility_of_element_located((By.XPATH, xpath_login_btn)))
    el_login_btn = driver.find_element(By.XPATH, value=xpath_login_btn)
    wbd = webdriver.ActionChains(driver).move_to_element(el_login_btn)
    time.sleep(1)
    wbd.click(el_login_btn).perform()
    time.sleep(1)
    # вводим имя
    xpath_element = "//input[@data-qa='login-input-username']"
    wait_el.until(EC.visibility_of_element_located((By.XPATH, xpath_element)))
    element = driver.find_element(By.XPATH, value=xpath_element)
    wbd = webdriver.ActionChains(driver).move_to_element(element)
    element.clear()
    element.send_keys(config.cnf["Login"]["username"])
    # вводим пароль
    xpath_element = "//input[@data-qa='login-input-password']"
    wait_el.until(EC.visibility_of_element_located((By.XPATH, xpath_element)))
    element = driver.find_element(By.XPATH, value=xpath_element)
    wbd = webdriver.ActionChains(driver).move_to_element(element)
    element.clear()
    element.send_keys(config.cnf["Login"]["password"])
    # кликаем на кнопку вход
    xpath_login_btn = "//button[@data-qa='account-login-submit']"
    wait_el.until(EC.visibility_of_element_located((By.XPATH, xpath_login_btn)))
    el_login_btn = driver.find_element(By.XPATH, value=xpath_login_btn)
    wbd = webdriver.ActionChains(driver).move_to_element(el_login_btn)
    time.sleep(1)
    wbd.click(el_login_btn).perform()
    time.sleep(1)
    print("*** Вошли на HH")

    if os.path.exists("Out\\urls_vacs.csv"):
        # читаем вакансии из файла
        with open("Out\\urls_vacs.csv", encoding="utf8") as f:
            print("Читаем вакансии из файла")
            reader = csv.reader(f)
            for row in reader:
                vacancies.append(row)
    else:
        # ищем живые вакансии с откликами
        soup = bs(driver.page_source, "lxml")
        try:
            vac_elements = soup.find_all("a", attrs={"data-qa": "vacancies-dashboard-vacancy-name"})
            for vacancy in vac_elements:
                url = vacancy.get("href")
                vacancies.append((url.split('/')[2].split('?')[0], vacancy.text, "https://hh.ru" + url))
        except:
            pass

        with open("Out\\urls_vacs.csv", "w", newline="", encoding="utf8") as f:
            writer = csv.writer(f)
            writer.writerows(vacancies)
    print(f"Найдено вакансий: {len(vacancies)}")
    if len(vacancies) > 0:
#
# перебираем вакансии получаем ссылки на резюме
#
        resume_ids = ""
        if os.path.exists("Out\\urls_resps.csv"):
            # читаем вакансии из файла
            with open("Out\\urls_resps.csv", encoding="utf8") as f:
                print("Читаем резюме из файла")
                reader = csv.reader(f)
                for row in reader:
                    urls_to_resume.append(row)
                    resume_ids += row[2].split('&')[1]
        else:
            # получаем ссылки на резюме через bs
            for resp_vacancy_id, resp_vacancy_title, vacancy_url in vacancies:
                print("*** Вакансия: ", resp_vacancy_title)
                resp_vacancy_url = f"https://hh.ru/employer/vacancyresponses?vacancyId={resp_vacancy_id}&hhtmFrom=employer_vacancies"        
                # находим все ссылки на откликнувшихся для этого резюме
                fl_start = True
                while fl_start:

                    try:
                        driver.get(resp_vacancy_url)
                    except WebDriverException:
                        time.sleep(1)
                    time.sleep(1)

                    soup = bs(driver.page_source, "lxml")

                    # получаем ссылки на резюме на этой странице
                    elements = soup.find_all("a", attrs={"data-qa": "resume-serp__resume-title"})
                    for u in elements:
                        url = r"https://hh.ru" + u.get("href")
                        resume_sign = url.split('&')[1]
                        if not (resume_sign in resume_ids):
                            # такой резюме еще не находили - добавляем
                            urls_to_resume.append((resp_vacancy_id, resp_vacancy_title, url, vacancy_url))
                            resume_ids += resume_sign   # собираем все добавленные id, что-бы удалить устареышие
                        else:
                            print(f"Повторяется: {resume_sign}")
                    try:
                        # ищем кнопку дальше
                        element = soup.find("a", attrs={"data-qa": "pager-next"})
                        resp_vacancy_url = r"https://hh.ru/employer/vacancyresponses" + element.get("href")
                        print('Следующая страница')
                    except:
                        # если кнопки дальше нет, то выходим
                        fl_start = False

            with open("Out\\urls_resps.csv", "w", newline="", encoding="utf8") as f:
                writer = csv.writer(f)
                writer.writerows(urls_to_resume)
#
# Начало разбора всех резюне
#
    if len(urls_to_resume) > 0:
        print("*** Всего найдено резюме: ", len(urls_to_resume))

        for r_vacancy_id, r_vacancy_title, r_resume_url, vacancy_url in urls_to_resume:
            r_resume_url = r_resume_url.replace("omsk.", "")
            resume_sign = r_resume_url.split('&')[1]

#            if os.path.exists(f"Out\\{resume_sign}.csv"):
#                # Если уже парсили - проверяем url вакансии
#                resave_response = False
#                with open(f"Out\\{resume_sign}.csv", encoding="utf8") as f:
#                    reader = csv.reader(f)
#                    for row in reader:
#                        if len(row) < 17:
#                            # Если урла нет - добавляем
#                            resave_response = True
#                            print("Нет URL")
#                            row.extend([vacancy_url])
#                if resave_response:
#                    with open(f"Out\\{resume_sign}.csv", "w", newline="", encoding="utf8") as f:
#                        writer = csv.writer(f)
#                        writer.writerows([row])
#   
            recheck_response = False
            if not os.path.exists(f"Out\\{resume_sign}.csv"):
                # Если новый отклик - парсим снова
                recheck_response = True

            if recheck_response:
                # ПАРСИМ
                res = []
                try:
                    driver.get(r_resume_url)
                except WebDriverException:
                    time.sleep(1)
                time.sleep(1)

                soup = bs(driver.page_source, "lxml")

                try:
                    r_element = soup.find("button", text="Показать все контакты")
                    # Открываем контакты - кликаем на показать
                    # Поставил пораньше, что-бы прогрузилось останьное на странице
                    # кликнуть <button type="button" data-qa="response-resume_show-phone-number" class="bloko-link bloko-link_pseudo">Показать все контакты</button>
                    xpath_view_btn = "//button[@data-qa='response-resume_show-phone-number']"
                    wait_el.until(EC.visibility_of_element_located((By.XPATH, xpath_view_btn)))
                    el_view_btn = driver.find_element(By.XPATH, value=xpath_view_btn)
                    wbd = webdriver.ActionChains(driver).move_to_element(el_view_btn)
                    time.sleep(1)
                    wbd.click(el_view_btn).perform()
                    time.sleep(1)
#                    print("Открываем контакт")
                except:
                    pass

                try:
                    r_element = soup.find("button", text="Раскрыть")
                    # Открываем сопроводительно письмо - кликаем на раскрыть
                    # Поставил пораньше, что-бы прогрузилось останьное на странице
                    # кликнуть <button type="button" class="bloko-link bloko-link_pseudo">Раскрыть</button>
                    xpath_view_btn = "//button[contains(text(), 'Раскрыть')]"
                    wait_el.until(EC.visibility_of_element_located((By.XPATH, xpath_view_btn)))
                    el_view_btn = driver.find_element(By.XPATH, value=xpath_view_btn)
                    wbd = webdriver.ActionChains(driver).move_to_element(el_view_btn)
                    time.sleep(1)
                    wbd.click(el_view_btn).perform()
                    time.sleep(1)
#                    print("Открываем сопроводительное письмо")
                except:
                    pass

                soup = bs(driver.page_source, "lxml")

                r_element = ''
                try:
                    # ДАТА ОТКЛИКА
                    # <div class="resume-sidebar-item__info" data-qa="resume-history-item-info"><div class="bloko-text bloko-text_tertiary">→ <!-- -->Отклик<!-- -->, <!-- -->28.06.22</div></div>
                    r_element = soup.find(attrs={"data-qa": "resume-history-item-info"}).text
                    r_element = r_element.split(",")[1].replace(" ", "")
                except:
                    pass
                res.append(r_element)

                r_element = ''
                try:
                    # ИМЯ
                    # <h2 data-qa="resume-personal-name" class="bloko-header-1"><span>Симоненко Арина Максимовна</span></h2>
                    r_element = soup.find(attrs={"data-qa": "resume-personal-name"}).text
                except AttributeError:
                    pass
                res.append(r_element)

                r_element = ''
                try:
                    # ПОЛ
                    # <span data-qa="resume-personal-gender">Женщина</span>
                    r_element = soup.find(attrs={"data-qa": "resume-personal-gender"}).text
                except AttributeError:
                    pass
                res.append(r_element)

                r_element = ''
                try:
                    # ВОЗРАСТ
                    # <span data-qa="resume-personal-age"><span>38<!-- -->&nbsp;<!-- -->лет</span></span>
                    r_element = soup.find(attrs={"data-qa": "resume-personal-age"}).text
                    r_element = r_element.replace("<!-- -->&nbsp;<!-- -->", "")
                except AttributeError:
                    pass
                res.append(r_element)

                r_element = ''
                try:
                    # ТЕЛЕФОН
                    # <div data-qa="resume-contacts-phone"><span data-qa="resume-contact-preferred">+7 (987) 822-26-47</span><div class="bloko-translate-guard"><div class="bloko-translate-guard">&nbsp;— предпочитаемый способ связи</div></div></div>
                    r_element = soup.find("span", attrs={"data-qa": "resume-contact-preferred"}).text
                except AttributeError:
                    try:
                        # А может быть так
                        # <div data-qa="resume-contacts-phone"><span class="bloko-icon bloko-icon_done bloko-icon_initial-secondary"></span>&nbsp;<span>+7 (913) 868-46-82</span><div class="bloko-translate-guard"></div><div class="resume-search-item-phone-verification-status"><div class="bloko-text bloko-text_small">Телефон подтвержден</div></div></div>
                        r_element = soup.find("div", attrs={"data-qa": "resume-contacts-phone"}).next_element.next_element.next_element.text.split("—")[0]
                        if ("+" not in r_element) and ("\(" not in r_element) and ("-" not in r_element):
                            raise AttributeError
                    except AttributeError:
                        try:
                            # А может быть так
                            # <div data-qa="resume-contacts-phone"><span>+7 (917) 640-41-85</span>
                            # <div data-qa="resume-contacts-phone"><span>+7 (977) 857-00-36</span><div class="bloko-translate-guard"></div></div>
                            r_element = soup.find("div", attrs={"data-qa": "resume-contacts-phone"}).text
                        except AttributeError:
                            try:
                                # А может быть так
                                # <p data-qa="anonymous-resume-warning-text" data-hidden-fields="phones, other_contacts">Соискатель скрыл <!-- -->телефон и дополнительные средства связи<!-- --> в&nbsp;резюме.</p>
                                r_element = soup.find("p", attrs={"data-qa": "anonymous-resume-warning-text"}).text.replace("<!-- -->", "").replace("&nbsp;", " ")
                            except AttributeError:
                                pass
                            pass
                res.append(r_element.replace("+", "").strip())

                r_element = ''
                try:
                    # EMAIL
                    # <div data-qa="resume-contact-email"><a href="mailto:Natali.EfimovaA@mail.ru"><span>Natali.EfimovaA@mail.ru</span></a></div>
                    # <div data-qa="resume-contact-email"><a href="mailto:adzhaga97@mail.ru" data-qa="resume-contact-preferred"><span>adzhaga97@mail.ru</span></a>&nbsp;— предпочитаемый способ связи</div>
                    r_element = soup.find(attrs={"data-qa": "resume-contact-email"}).text.split("—")[0].strip()
                except AttributeError:
                    pass
                res.append(r_element)

                r_location = ''
                r_mobility = ''
                try:
                # АДРЕСС
                # МОБИЛЬНОСТЬ
                # <p><span data-qa="resume-personal-address">Москва</span>, <!-- -->не готова к переезду<!-- -->, <!-- -->не готова к командировкам</p>
                    loc_mob = soup.find(attrs={"data-qa": "resume-personal-address"}).previous_element.text
                    loc_mob = loc_mob.split(",")
                    if len(loc_mob) == 4:
                        r_location = loc_mob[0] + "," + loc_mob[1]
                        r_mobility = ','.join(loc_mob[2:])[1:]
                    else:
                        r_location = loc_mob[0]
                        r_mobility = ','.join(loc_mob[1:])[1:]
                except AttributeError:
                    pass
                res.append(r_location)
                res.append(r_mobility)

                r_element = ""
                try:
                    # ДОЛЖНОСТЬ
                    # <span class="resume-block__title-text" data-qa="resume-block-title-position"><span>Менеджер-администратор</span></span>
                    r_element = soup.find(attrs={"data-qa": "resume-block-title-position"}).text
                except AttributeError:
                    pass
                res.append(r_element)

                r_element = ""
                try:
                    # ЗАРПЛАТА
                    # <span class="resume-block__salary resume-block__title-text_salary" data-qa="resume-block-salary">50 000<!-- -->&nbsp;<!-- -->руб.</span>
                    r_element = soup.find(attrs={"data-qa": "resume-block-salary"}).text.replace(" ", "").replace("\u2009", "").replace("\xa0", "").replace("руб.", "")
                except AttributeError:
                    pass
                res.append(r_element)

                r_element = ""
                try:
                    # ПОСЛЕДНЕЕ МЕСТО РАБОТЫ
                    # <a class="bloko-link bloko-link_kind-tertiary" href="/employer/669587?hhtmFrom=resume"><span>ЭТАЖИ, агентство недвижимости</span></a>
                    # <div class="resume-block-container"><div class="bloko-text bloko-text_strong"><span>ГРУППА КОМПАНИЙ ,,СОНЭС,,</span></div>
                    r_element = soup.find(attrs={"class": "bloko-text bloko-text_strong"}).text
                except:
                    try:
                        # <a class="bloko-link bloko-link_kind-tertiary" href="/employer/669587?hhtmFrom=resume"><span>ЭТАЖИ, агентство недвижимости</span></a>
                        r_element = soup.find(attrs={"class": "bloko-link bloko-link_kind-tertiary"}).text
                    except:
                        pass
                res.append(r_element)

                r_element = ""
                try:
                    # ДОЛЖНОСТЬ НА ПОСЛЕДНЕМ МЕСТЕ РАБОТЫ
                    # <div data-qa="resume-block-experience-position" class="bloko-text bloko-text_strong"><span>Специалист по недвижимости</span></div>
                    r_element = soup.find(attrs={"data-qa": "resume-block-experience-position"}).text
                except:
                    pass
                res.append(r_element)

                r_element = ""
                try:
                    # ОПЫТ ВОЖДЕНИЯ
                    # https://omsk.hh.ru/resume/77e72e370008415215004ca8454e6955456343?hhtmFromLabel=related_resumes&hhtmFrom=resume
                    # <span class="resume-block__title-text resume-block__title-text_sub">Опыт вождения</span>
                    # <div class="resume-block-container">Права категории<!-- -->&nbsp;<!-- -->B, C</div>
                    r_element = soup.find(attrs={"data-qa": "resume-block-driver-experience"}).text.replace("Опыт вождения","")
                except:
                    pass
                res.append(r_element)

                r_element = ""
                try:
                    # СОПРОВОДИТЕЛЬНОЕ ПИСЬМО
                    # https://omsk.hh.ru/resume/2c6eb6be000aff4a50004ca8454e3758475879?vacancyId=66922156&resumeId=184502864&t=2760073550&chatId=2756370174&page=0&collection=response&hhtmFrom=employer_vacancy_responses
                    # <div class="bloko-gap bloko-gap_top"><div class="resume-block"><div class="bloko-column bloko-column_xs-4 bloko-column_s-8 bloko-column_m-9 bloko-column_l-12"><div class="resume-block-letter__full-text"><span>Здравствуйте.<br><br>Меня зовут Анастасия Уварова.<br><br>Я имею опыт управленческой деятельности более 14 лет.<br><br>За этот период открыла 4 проекта с нуля.<br>Большая часть моего опыта - это функционал HR, подбор персонала.<br><br>Самостоятельно занималась поиском сотрудников, размещала вакансии, проводила собеседования, адаптировала и обучала сотрудников.<br><br>На данный момент рассматриваю дополнительную занятость, планирую совмещать с основной работой.<br><br>Готова пройти собеседование в вашей компании.</span>
                    r_element = soup.find(attrs={"class": "resume-block-letter__full-text"}).text
                except:
                    pass
                res.append(r_element)

                res.insert(0, r_vacancy_title)
                res.extend([r_resume_url])
                res.extend([vacancy_url])
                if len(res[5]) > 0 or len(res[6]) > 0:
                    # если есть телефон или emain, скорее всего разобрали нормально - записываем
                    print(f"{res[2]} {res[5]} {res[6]}")
                    with open(f"Out\\{resume_sign}.csv", "w", newline="", encoding="utf8") as f:
                        writer = csv.writer(f)
                        writer.writerows([res])
                else:
                    print(f"- РЕКЛАМА")
#
# Удаляем старые, не актуальные резюме и файлы
#
        if config.cnf["Prg"]["delete_old"] == "True":
            content = os.listdir('Out')
            num_deleted = 0
            for file_name in content:
                if ("resumeId=" in file_name) and (file_name.split(".")[0] not in resume_ids):
                    os.remove(f"Out\\{file_name}")
                    num_deleted += 1
            print(f"*** Удалено {num_deleted} старых файлов")

    if config.cnf["Debug"]["debuging"] == "False":
        if os.path.exists("Out\\urls_vacs.csv"):
            os.remove("Out\\urls_vacs.csv")
        if os.path.exists("Out\\urls_resps.csv"):
            os.remove("Out\\urls_resps.csv")

    driver.close()

    print("*** Стоп")

# В каталог Out складываем результаты для каждого сайта в отдельный файл
# Создаем Out если отсутствует
if not os.path.exists("Out"):
    os.mkdir("Out")

tic = time.perf_counter()
grab_hh()
save_result()
toc = time.perf_counter()

print("*** Данные сохранены")
print(f"*** Время выполнения: {toc-tic}")
print("*** Нажмите <ENTER>")
input()

