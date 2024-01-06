import os
import requests
import numpy as np
from terminaltables import AsciiTable
from dotenv import load_dotenv


def draw_table(stats, table_title):
    TABLE_DATA = [('Язык программирования', 'Вакансий найдено',
                   'Вакансий обработано', 'Средняя зарплата')]
    TABLE_DATA += [(k, *v.values()) for k, v in stats.items()]
    table_instance = AsciiTable(TABLE_DATA, table_title)
    print(table_instance.table)
    print()


def predict_rub_salary_for_superJob(vacancy):
    if vacancy is None or vacancy['currency'] != 'rub':
        return None

    if vacancy['payment_from'] == 0 and vacancy['payment_to'] == 0:
        return None
    elif vacancy['payment_from'] == 0:
        return int(vacancy['payment_to']*0.8)
    elif vacancy['payment_to'] == 0:
        return int(vacancy['payment_from']*1.2)
    else:
        return (vacancy['payment_to'] + vacancy['payment_from']) // 2


def get_salaries_superJob(superjob_token):
    MOSCOW_ID = 4
    VACANCIES_PER_PAGE = 100
    prog_lang_vacancies = {}
    prog_langs = ['JavaScript', 'Java', 'Python',
                  'Ruby', 'PHP', 'C++', 'C#', 'C', 'Go', 'Swift', 'Scala']
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': superjob_token}
    params = {
        'prog_langword': '',
        'profession_only': 1,
        'town': MOSCOW_ID,
        'page': 0,
        'count': VACANCIES_PER_PAGE
    }
    for prog_lang in prog_langs:
        params['prog_langword'] = f'программист {prog_lang}'
        params['page'] = 0
        response = requests.get(url, headers=headers, params=params)
        vacancies = response.json()

        prog_lang_vacancies[prog_lang] = {}
        prog_lang_vacancies[prog_lang]['vacancies_found'] = vacancies['total']
        prog_lang_vacancies[prog_lang]['vacancies_processed'] = 0
        prog_lang_vacancies[prog_lang]['average_salary'] = 0

        vacancies_arr = np.empty(shape=[1, 0])
        page = 0
        while True:
            params['prog_langword'] = f'программист {prog_lang}'
            params['page'] = page
            response = requests.get(url, headers=headers, params=params)
            vacancies = response.json()
            for i in range(len(vacancies['objects'])):
                vacancies_arr = np.append(vacancies_arr,
                                          vacancies['objects'][i])

            vacancies_arr = vacancies_arr[vacancies_arr != np.array(None)]
            salary = np.array(
                list(map(predict_rub_salary_for_superJob, vacancies_arr)))
            salary = salary[salary != np.array(None)]

            if len(salary) > 0:
                prog_lang_vacancies[prog_lang]['vacancies_processed'] = len(
                    salary)
                prog_lang_vacancies[prog_lang]['average_salary'] = np.mean(
                    salary, dtype='int64')

            page += 1
            if not vacancies['more']:
                break
    return prog_lang_vacancies


def predict_rub_salary(vacancy):
    if vacancy is None or vacancy['currency'] != 'RUR':
        return None

    if vacancy['from'] is None and vacancy['to'] is None:
        return None
    elif vacancy['from'] is None:
        return int(vacancy['to']*0.8)
    elif vacancy['to'] is None:
        return int(vacancy['from']*1.2)
    else:
        return (vacancy['to'] + vacancy['from']) // 2


def get_salaries_hh():
    MOSCOW_ID = 1
    VACANCIES_PER_PAGE = 100
    SEARCH_PERIOD_DAYS = 30
    prog_lang_vacancies = {}
    prog_langs = ['JavaScript', 'Java', 'Python',
                  'Ruby', 'PHP', 'C++', 'C#', 'C', 'Go', 'Swift', 'Scala']
    url = 'https://api.hh.ru/vacancies'
    params = {
        'text': '',
        'area': MOSCOW_ID,
        'search_period': SEARCH_PERIOD_DAYS,
        'per_page': VACANCIES_PER_PAGE
    }
    for prog_lang in prog_langs:
        params['text'] = f'программист {prog_lang}'
        response = requests.get(url, params=params)
        response.raise_for_status()
        vacancies = response.json()

        prog_lang_vacancies[prog_lang] = {}
        prog_lang_vacancies[prog_lang]['vacancies_found'] = vacancies['found']
        prog_lang_vacancies[prog_lang]['vacancies_processed'] = 0
        prog_lang_vacancies[prog_lang]['average_salary'] = 0

        vacancies_arr = np.empty(shape=[1, 0])
        pages = vacancies['pages']
        for page in range(pages):
            params['page'] = page
            response = requests.get(url, params=params)
            response.raise_for_status()
            vacancies = response.json()
            for i in range(len(vacancies['items'])):
                vacancies_arr = np.append(vacancies_arr,
                                          vacancies['items'][i]['salary'])

        vacancies_arr = vacancies_arr[vacancies_arr != np.array(None)]
        salary = np.array(list(map(predict_rub_salary, vacancies_arr)))
        salary = salary[salary != np.array(None)]

        if len(salary) > 0:
            prog_lang_vacancies[prog_lang]['average_salary'] = np.mean(
                salary, dtype='int64')
            prog_lang_vacancies[prog_lang]['vacancies_processed'] = len(salary)

    return prog_lang_vacancies


if __name__ == '__main__':
    load_dotenv()
    superjob_token = os.environ['SUPERJOB_API_prog_lang']

    salaries_superJob = get_salaries_superJob(superjob_token)
    draw_table(salaries_superJob, 'SuperJob Moscow')

    salaries_hh = get_salaries_hh()
    draw_table(salaries_hh, 'HeadHunter Moscow')
