from unicodedata import normalize
import re
import json
import requests
import random
from colorama import Fore, Style
from fake_headers import Headers
from progress.bar import ChargingBar
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from webdriver_manager.chrome import ChromeDriverManager


def wait_element(browser_, delay_second=2, by=By.CLASS_NAME, value=None):
    return WebDriverWait(browser_, delay_second).until(
        expected_conditions.presence_of_element_located((by, value))
    )


def gen_headers():
    browser_ = random.choice(['chrome', 'firefox', 'opera'])
    os = random.choice(['win', 'mac', 'lin'])
    headers = Headers(browser=browser_, os=os)
    return headers.generate()


chrome_path = ChromeDriverManager().install()

browser_service = Service(executable_path=chrome_path)

browser = Chrome(service=browser_service)

browser.get('https://spb.hh.ru/search/vacancy?text=python&area=1&area=2')

html_page = browser.page_source
# print(len(html_page))


main_soup = BeautifulSoup(html_page, 'lxml')

list_vacancy = main_soup.find('main', 'vacancy-serp-content')
vacancy = list_vacancy.find_all('div', 'vacancy-serp-item__layout')
print(f'Вакансий на странице - {len(vacancy)}')

total_list = []

for element in vacancy:
    title = element.find('span', 'serp-item__title-link-wrapper').find('span', 'serp-item__title').text
    company = element.find(name='div', attrs='vacancy-serp-item-company').find(name='span')
    if company is None:
        company = element.find(name='div', attrs='vacancy-serp-item__meta-info-company').text
    else:
        company = element.find(name='div', attrs='vacancy-serp-item-company').find(name='span').text

    city = element.find(name='div', attrs={
        'data-qa': 'vacancy-serp__vacancy-address',
        'class': 'bloko-text'
    }).text
    salary = element.find(name='span', attrs={
        'class': 'bloko-header-section-2',
        'data-qa': 'vacancy-serp__vacancy-compensation'
    })
    if salary is None:
        salary = 'Не указано'
    else:

        salary = element.find(name='span', attrs={
            'class': 'bloko-header-section-2',
            'data-qa': 'vacancy-serp__vacancy-compensation'
        }).text

    link = element.find(name='a', attrs='bloko-link')['href']

    total_list.append({
        'title': normalize('NFKD', title),
        'company': normalize('NFKD', company),
        'city': normalize('NFKD',city),
        'salary': normalize('NFKD', salary),
        'link': link
    })


vacancy_dict = {}
step = 1

bar = ChargingBar('Поиск', max=len(total_list))

for vacancy in total_list:
    response = requests.get(vacancy['link'], headers=gen_headers())
    if 200 <= response.status_code < 300:
        main_html_2 = response.text
        main_soup_2 = BeautifulSoup(main_html_2, 'lxml')
        description = main_soup_2.find_all(name=['p', 'li'])
        str_description = ''
        for i in description:
            str_description += i.text

        pattern = r"django|flask"
        result = re.search(pattern, str_description.lower())

        if result is not None:
            vacancy_dict[str(step)] = vacancy
            step += 1

    else:
        print(Fore.RED, response.status_code)
        print(Style.RESET_ALL)
    bar.next()

bar.finish()

if len(vacancy_dict) > 0:

    with open('result_2.json', 'w', encoding='utf-8') as f:
        json.dump(vacancy_dict, f, indent=4, ensure_ascii=False)
    print('Результат поиска записан в - result_2.json')

