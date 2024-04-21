import re
import json
from unicodedata import normalize
import requests
import random
from bs4 import BeautifulSoup
from colorama import Fore, Style
from fake_headers import Headers
from progress.bar import ChargingBar


'''Периодически в response.text приходит не полный html-код страницы и тег "vacancy-serp-item__layout"
в этом коде отсутствует, соответственно вакансии на странице не находятся. При повторном запуске парсера проблема может 
уйти и в response.text приходит html-код с нужным тегом
При выводе в консоль "Вакансий на странице - 0" просьба перезапустить парсер.
Не нашел решения этой проблемы.'''



def gen_headers():
    browser = random.choice(['chrome', 'firefox', 'opera'])
    os = random.choice(['win', 'mac', 'lin'])
    headers = Headers(browser=browser, os=os)
    return headers.generate()


response = requests.get('https://spb.hh.ru/search/vacancy?text=python&area=1&area=2', headers=gen_headers())

total_list = []

if 200 <= response.status_code < 300:
    print(Fore.GREEN, response.status_code)
    print(Style.RESET_ALL)

    main_html = response.text
    # print(len(main_html))
    main_soup = BeautifulSoup(main_html, 'lxml')

    list_vacancy = main_soup.find('main', 'vacancy-serp-content')
    vacancy = list_vacancy.find_all('div', 'vacancy-serp-item__layout')
    print(f'Вакансий на странице - {len(vacancy)}')

    for element in vacancy:
        title = element.find('span', 'serp-item__title-link-wrapper').find('span', 'serp-item__title').text
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
            'city': normalize('NFKD', city),
            'salary': normalize('NFKD', salary),
            'link': link
        })
else:
    print(Fore.RED, response.status_code)
    print(Style.RESET_ALL)

vacancy_dict = {}

step = 1

bar = ChargingBar('Поиск', max=len(total_list))

for vacancy in total_list:
    response = requests.get(vacancy['link'], headers=gen_headers())
    if 200 <= response.status_code < 300:
        # print(Fore.GREEN, response.status_code)
        # print(Style.RESET_ALL)

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
    with open('result_1.json', 'w', encoding='utf-8') as f:
        json.dump(vacancy_dict, f, indent=4, ensure_ascii=False)
    print('Результат поиска записан в - result_1.json')
