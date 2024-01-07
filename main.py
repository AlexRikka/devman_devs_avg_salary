import os
import requests
from terminaltables import AsciiTable
from dotenv import load_dotenv


def draw_table(stats, table_title):
    salary_table = [('Язык программирования', 'Вакансий найдено',
                     'Вакансий обработано', 'Средняя зарплата')]
    salary_table += [(k, *v.values()) for k, v in stats.items()]
    table_instance = AsciiTable(salary_table, table_title)
    print(table_instance.table)
    print()


def predict_rub_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_to + salary_from) // 2
    elif salary_to:
        return int(salary_to*0.8)
    elif salary_from:
        return int(salary_from*1.2)
    else:
        return None


def predict_rub_salary_for_superJob(vacancy):
    if vacancy and vacancy['currency'] == 'rub':
        return predict_rub_salary(vacancy['payment_from'],
                                  vacancy['payment_to'])
    else:
        return None


def predict_rub_salary_for_hh(vacancy):
    if vacancy and vacancy['currency'] == 'RUR':
        return predict_rub_salary(vacancy['from'], vacancy['to'])
    else:
        return None


def get_salaries_for_superJob(superjob_token):
    moscow_id = 4
    vacancies_per_page = 100
    vacancies_stats = {}
    programming_languages = ['JavaScript', 'Java', 'Python',
                             'Ruby', 'PHP', 'C++', 'C#', 'C',
                             'Go', 'Swift', 'Scala']
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': superjob_token}
    params = {
        'keyword': '',
        'profession_only': 1,
        'town': moscow_id,
        'page': 0,
        'count': vacancies_per_page
    }

    for language in programming_languages:
        params['keyword'] = f'программист {language}'
        vacancies_stats[language] = {
            'vacancies_found': 0,
            'vacancies_processed': 0,
            'average_salary': 0
        }

        salary_summ = 0
        salary_count = 0
        page = 0
        while True:
            params['page'] = page
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            vacancies = response.json()
            vacancies_stats[language]['vacancies_found'] = vacancies['total']

            for vacancy in vacancies['objects']:
                salary = predict_rub_salary_for_superJob(vacancy)
                if salary:
                    salary_summ += salary
                    salary_count += 1

            page += 1
            if not vacancies['more']:
                break

        vacancies_stats[language]['vacancies_processed'] = salary_count
        vacancies_stats[language]['average_salary'] = salary_summ // \
            salary_count if salary_count != 0 else 0

    return vacancies_stats


def get_salaries_for_hh():
    moscow_id = 1
    vacancies_per_page = 100
    search_period_days = 30
    vacancies_stats = {}
    programming_languages = ['JavaScript', 'Java', 'Python',
                             'Ruby', 'PHP', 'C++', 'C#', 'C',
                             'Go', 'Swift', 'Scala']
    url = 'https://api.hh.ru/vacancies'
    params = {
        'text': '',
        'area': moscow_id,
        'search_period': search_period_days,
        'per_page': vacancies_per_page
    }

    for language in programming_languages:
        params['text'] = f'программист {language}'
        vacancies_stats[language] = {
            'vacancies_found': 0,
            'vacancies_processed': 0,
            'average_salary': 0
        }

        salary_summ = 0
        salary_count = 0
        page = 0
        while True:
            params['page'] = page
            response = requests.get(url, params=params)
            response.raise_for_status()
            vacancies = response.json()
            vacancies_stats[language]['vacancies_found'] = vacancies['found']

            for vacancy in vacancies['items']:
                salary = predict_rub_salary_for_hh(
                    vacancy['salary'])
                if salary:
                    salary_summ += salary
                    salary_count += 1

            page += 1
            if page == vacancies['pages']:
                break

        vacancies_stats[language]['vacancies_processed'] = salary_count
        vacancies_stats[language]['average_salary'] = salary_summ // \
            salary_count if salary_count != 0 else 0

    return vacancies_stats


def main():
    load_dotenv()
    superjob_token = os.environ['SUPERJOB_API_KEY']

    salaries_superJob = get_salaries_for_superJob(superjob_token)
    draw_table(salaries_superJob, 'SuperJob Moscow')

    salaries_hh = get_salaries_for_hh()
    draw_table(salaries_hh, 'HeadHunter Moscow')


if __name__ == '__main__':
    main()
