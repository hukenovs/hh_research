"""
------------------------------------------------------------------------

Title         : hh_research.py
Author        : Alexander Kapitanov
E-mail        : sallador@bk.ru
Lang.         : python
Company       :
Release Date  : 2019/08/14

------------------------------------------------------------------------

Description   :
    HeadHunter (hh.ru) research script.

    1. Get data from hh.ru by user request (i.e. 'Machine learning')
    2. Collect all vacancies.
    3. Parse JSON and get useful values: salary, experience, name,
    skills, employer name etc.
    4. Calculate some statistics: average salary, median, std, variance

------------------------------------------------------------------------

GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (c) 2019 Kapitanov Alexander

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

THERE IS NO WARRANTY FOR THE PROGRAM, TO THE EXTENT PERMITTED BY
APPLICABLE LAW. EXCEPT WHEN OTHERWISE STATED IN WRITING THE COPYRIGHT
HOLDERS AND/OR OTHER PARTIES PROVIDE THE PROGRAM "AS IS" WITHOUT
WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT
NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND
PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE
DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR OR
OR CORRECTION.

------------------------------------------------------------------------
"""
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from tqdm import tqdm

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

import requests
import argparse
import hashlib
import pickle
import nltk
import re
import os

# nltk.download('stopwords')

CACHE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'cache')
API_BASE_URL = 'https://api.hh.ru/vacancies'

DEFAULT_PARAMETERS = {
    'area': 1,
    'per_page': 50,
}

HH_URL = API_BASE_URL + '?' + urlencode(DEFAULT_PARAMETERS)

EX_URL = 'https://api.exchangerate-api.com/v4/latest/RUB'
MAX_WORKERS = int(os.getenv('MAX_WORKERS', 5))

exchange_rates = {}


def update_exchange_rates():
    """
    Parse exchange rate for RUB, USD, EUR and save them to `exchange_rates`
    """
    try:
        print('Try to get rates from URL...')
        resp = requests.get(EX_URL)
        rates = resp.json()['rates']

    except requests.exceptions.SSLError:
        print('Cannot get exchange rate! Try later or change host API')
        exit('Exit from script. Cannot get data from URL!')

    for curr in ['RUB', 'USD', 'EUR']:
        exchange_rates[curr] = rates[curr]

    # Change 'RUB' to 'RUR'
    exchange_rates['RUR'] = exchange_rates.pop('RUB')
    print(f'Get exchange rates: {exchange_rates}')


def clean_tags(str_html):
    """
    Remove HTML tags from string (text)

    Parameters
    ----------
    str_html: str
        Input string with tags

    Returns
    -------
    string
        Clean text without tags

    """
    pat = re.compile('<.*?>')
    res = re.sub(pat, '', str_html)
    return res


def get_vacancy(vacancy_id):
    # Vacancy URL
    url = f'https://api.hh.ru/vacancies/{vacancy_id}'
    vacancy = requests.api.get(url).json()

    # Extract salary
    salary = vacancy['salary']

    # Calculate salary:
    # Get salary into {RUB, USD, EUR} with {Gross} parameter and
    # return a new salary in RUB.
    cl_ex = {'from': None, 'to': None}
    if salary:
        # fn_gr = lambda: 0.87 if vsal['gross'] else 1
        def fn_gr():
            return 0.87 if vacancy['salary']['gross'] else 1

        for i in cl_ex:
            if vacancy['salary'][i] is not None:
                cl_ex[i] = int(
                    fn_gr() * salary[i] / exchange_rates[salary['currency']]
                )

    # Create pages tuple
    return (
        vacancy_id,
        vacancy['employer']['name'],
        vacancy['name'],
        salary is not None,
        cl_ex['from'],
        cl_ex['to'],
        vacancy['experience']['name'],
        vacancy['schedule']['name'],
        [el['name'] for el in vacancy['key_skills']],
        clean_tags(vacancy['description']),
    )


def get_vacancies(query, refresh=False):
    """
    Parse vacancy JSON: get vacancy name, salary, experience etc.

    Parameters
    ----------
    query: str
        Search query
    refresh: bool
        Refresh cached data

    Returns
    -------
    list
        List of useful arguments from vacancies

    """
    cache_hash = hashlib.md5(query.encode()).hexdigest()
    cache_file_name = os.path.join(CACHE_DIR, cache_hash)
    try:
        if not refresh:
            return pickle.load(open(cache_file_name, 'rb'))

    except (FileNotFoundError, pickle.UnpicklingError):
        pass

    ids = []
    parameters = {'text': query, **DEFAULT_PARAMETERS}
    url = API_BASE_URL + '?' + urlencode(parameters)
    nm_pages = requests.get(url).json()['pages']
    for i in range(nm_pages + 1):
        resp = requests.get(url, {'page': i})
        ids.extend(x['id'] for x in resp.json()['items'])

    vacancies = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for vacancy in tqdm(executor.map(get_vacancy, ids), total=len(ids)):
            vacancies.append(vacancy)

    pickle.dump(vacancies, open(cache_file_name, 'wb'))
    return vacancies


def prepare_df(dct_df):
    """
    Prepare data frame and save results

    Parameters
    ----------
    dct_df: list
        List of parsed json dicts

    """
    # List of columns
    df_cols = ['Id',
               'Employer',
               'Name',
               'Salary',
               'From',
               'To',
               'Experience',
               'Schedule',
               'Keys',
               'Description',
               ]
    # Create pandas dataframe
    df = pd.DataFrame(data=dct_df, columns=df_cols)
    # Print some info from data frame
    print(
        df[df['Salary']][['Employer', 'From', 'To', 'Experience', 'Schedule']][0:10]
    )
    # Save to file
    df.to_csv(r'hh_data.csv', index=False)


def analyze_df():
    """
    Load data frame and analyze results

    """

    sns.set()
    print('\n\nLoad table and analyze results:')
    df = pd.read_csv('hh_data.csv')
    print(df[df['Salary']][0:7])

    print('\nNumber of vacancies: {}'.format(df['Id'].count()))
    print('\nVacancy with max salary: ')
    print(df.iloc[df[['From', 'To']].idxmax()])
    print('\nVacancy with min salary: ')
    print(df.iloc[df[['From', 'To']].idxmin()])

    print('\nDescribe salary data frame: ')
    df_stat = df[['From', 'To']].describe().applymap(np.int32)
    print(df_stat.iloc[list(range(4)) + [-1]])

    print('\nAverage statistics (average filter for "From"-"To" parameters):')
    comb_from_to = np.nanmean(df[df['Salary']][['From', 'To']].to_numpy(), axis=1)
    print('Describe salary series:')
    print('Min    : %d' % np.min(comb_from_to))
    print('Max    : %d' % np.max(comb_from_to))
    print('Mean   : %d' % np.mean(comb_from_to))
    print('Median : %d' % np.median(comb_from_to))

    print('\nMost frequently used keys in the all vacancies:')
    # Collect keys from df
    keys_df = df['Keys'].to_list()
    # Create a list of keys for all vacancies
    lst_keys = []
    for keys_elem in keys_df:
        for el in keys_elem[1:-1].split(', '):
            if el != '':
                lst_keys.append(re.sub('\'', '', el.lower()))
    # Unique keys and their counter
    set_keys = set(lst_keys)
    # Dict: {Key: Count}
    dct_keys = {el: lst_keys.count(el) for el in set_keys}
    # Sorted dict
    srt_keys = dict(sorted(dct_keys.items(), key=lambda x: x[1], reverse=True))
    # Return pandas series
    most_keys = pd.Series(srt_keys, name='Keys')
    print(most_keys[:7])

    print('\nMost frequently used words in the all vacancies:')
    # Collect keys from df
    words_df = df['Description'].to_list()
    # Long string - combine descriptions
    words_ls = ' '.join(
        [re.sub(' +', ' ', re.sub('\d+', '', el.strip().lower())) for el in words_df]
    )
    # Find all words
    words_re = re.findall('[a-zA-Z]+', words_ls)
    # Filter words with length < 3
    words_l2 = [el for el in words_re if len(el) > 2]
    # Unique words
    words_st = set(words_l2)
    # Remove 'stop words'
    stop_words = set(nltk.corpus.stopwords.words('english'))
    # XOR for dictionary
    words_st ^= stop_words
    words_st ^= {'amp', 'quot'}
    # Dictionary - {Word: Counter}
    words_cnt = {el : words_l2.count(el) for el in words_st}
    # Pandas series
    most_words = pd.Series(dict(sorted(words_cnt.items(), key=lambda x: x[1], reverse=True)))
    print(most_words[:7])

    print('\nPlot results. Close figure box to continue...')
    fz = plt.figure(figsize=(12, 4), dpi=80)
    fz.add_subplot(1, 2, 1)
    plt.title('From / To Box-plot')
    sns.boxplot(data=df[['From', 'To']].dropna(), width=0.4)
    fz.add_subplot(1, 2, 2)
    plt.title('From / To Swarm-plot')
    sns.swarmplot(data=df[['From', 'To']].dropna(), size=6)
    plt.tight_layout()
    plt.show()


def run():
    """
    Main function - combine all methods together

    """
    parser = argparse.ArgumentParser()
    parser.add_argument('query', help='Search query (e.g. "Machine learning")')
    parser.add_argument(
        '--refresh', help='Refresh cached data from HH API', action='store_true',
        default=False,
    )
    args = parser.parse_args()

    update_exchange_rates()
    print('Collect data from JSON. Create list of vacancies...')
    vac_list = get_vacancies(args.query, args.refresh)
    print('Prepare data frame...')
    prepare_df(vac_list)
    analyze_df()
    print('Done! Exit()')


if __name__ == "__main__":
    run()
