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
    prog_lang_vacancies = {}
    prog_langs_keys = ['JavaScript', 'Java', 'Python',
                       'Ruby', 'PHP', 'C++', 'C#', 'C', 'Go', 'Swift', 'Scala']
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': superjob_token}
    params = {
        'keyword': '',
        'profession_only': 1,
        'town': 4,
        'page': 0,
        'count': 100
    }
    for key in prog_langs_keys:
        params['keyword'] = f'программист {key}'
        params['page'] = 0
        response = requests.get(url, headers=headers, params=params)
        vacancies = response.json()

        prog_lang_vacancies[key] = {}
        prog_lang_vacancies[key]['vacancies_found'] = vacancies['total']
        prog_lang_vacancies[key]['vacancies_processed'] = 0
        prog_lang_vacancies[key]['average_salary'] = 0

        vacancies_arr = np.empty(shape=[1, 0])
        page = 0
        while True:
            params['keyword'] = f'программист {key}'
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
                prog_lang_vacancies[key]['vacancies_processed'] = len(salary)
                prog_lang_vacancies[key]['average_salary'] = np.mean(
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
    prog_lang_vacancies = {}
    prog_langs_keys = ['JavaScript', 'Java', 'Python',
                       'Ruby', 'PHP', 'C++', 'C#', 'C', 'Go', 'Swift', 'Scala']
    url = 'https://api.hh.ru/vacancies'
    params = {
        'text': '',
        'area': 1,  # Москва
        'search_period': 30,  # дни
        'per_page': 100
    }
    for key in prog_langs_keys:
        params['text'] = f'программист {key}'
        response = requests.get(url, params=params)
        response.raise_for_status()
        vacancies = response.json()

        prog_lang_vacancies[key] = {}
        prog_lang_vacancies[key]['vacancies_found'] = vacancies['found']
        prog_lang_vacancies[key]['vacancies_processed'] = 0
        prog_lang_vacancies[key]['average_salary'] = 0

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
            prog_lang_vacancies[key]['average_salary'] = np.mean(
                salary, dtype='int64')
            prog_lang_vacancies[key]['vacancies_processed'] = len(salary)

    return prog_lang_vacancies


if __name__ == '__main__':
    load_dotenv()
    superjob_token = os.environ['SUPERJOB_API_KEY']

    salaries_superJob = get_salaries_superJob(superjob_token)
    draw_table(salaries_superJob, 'SuperJob Moscow')

    salaries_hh = get_salaries_hh()
    draw_table(salaries_hh, 'HeadHunter Moscow')
