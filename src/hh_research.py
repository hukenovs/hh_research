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
import re
import requests
import pandas as pd


def form_url():
    """
    Create full URL by using input parameters

    Returns
    -------
    string
        Full URL for requests

    """
    hh_url = 'https://api.hh.ru/vacancies?'
    hh_dct = {
        'area': 1,
        'text': 'Machine learning',
        'per_page': 50,
    }
    hh_lst = '&'.join([i + '=' + str(hh_dct[i]).replace(' ', '+') for i in hh_dct])
    return hh_url + hh_lst


HH_URL = form_url()
EX_URL = 'https://api.exchangerate-api.com/v4/latest/RUB'


def get_exchange(ex_url):
    """
    Parse exchange rate for RUB, USD, EUR and return them as dict

    Parameters
    ----------
    ex_url: str
        URL for website which can return json

    Returns
    -------
    dict
        Dictionary for exchange rates (RUB, USD, EUR)

    """
    try:
        print('Try to get rates from URL...')
        with requests.get(ex_url) as curr:
            rates = curr.json()['rates']
            drate = {el: rates[el] for el in ['RUB', 'USD', 'EUR']}
            print(
                'Get exchange rates: {}'.format(drate))
            # Change 'RUB' to 'RUR'
            drate['RUR'] = drate.pop('RUB')
            return drate
    except requests.exceptions.SSLError:
        print('Cannot get exchange rate! Try later or change host API')
        exit('Exit from script. Cannot get data from URL!')


def get_list_id():
    """
    Check if file with vacancy IDs exists.

    Get ID list and save it to file if doesn't exist.
    Request: GET data from URL by using JSON.

    Returns
    -------
    list
        ID list for vacancies

    """
    fname = 'id_list.dat'
    try:
        with open(fname) as f:
            print('File with IDs exists. Read file...')
            return [el.rstrip() for el in f]
    except IOError:
        print('File with IDs does not exist. Create file...')

        id_lst = []
        nm_pages = requests.api.get(HH_URL).json()['pages']
        for i in range(nm_pages + 1):
            page_url = HH_URL + f'&page={i}'
            page_req = requests.api.get(page_url).json()['items']
            for el in page_req:
                id_lst.append(el['id'])

        with open(fname, 'w') as f:
            for el in id_lst:
                f.write("%s\n" % el)
        return id_lst


def clean_tags(str_html):
    """
    Remove HTML tags from string (text)

    Returns
    -------
    string
        Clean text without tags

    """
    pat = re.compile('<.*?>')
    res = re.sub(pat, '', str_html)
    return res


def get_vacancies(ids, exc):
    """
    Parse vacancy JSON: get vacancy name, salary, experience etc.

    Parameters
    ----------
    ids: list
        list of vacancies
    exc: dict
        Exchange rates as dictionary: RUR, USD, EUR

    Returns
    -------
    dict
        List of useful arguments from vacancies

    """
    ret_lst = []
    for el in ids:
        # Vacancy URL
        pages_req = requests.api.get('https://api.hh.ru/vacancies/' + el).json()

        # Extract salary
        salary = pages_req['salary']

        # Calculate salary:
        # Get salary into {RUB, USD, EUR} with {Gross} parameter and
        # return a new salary in RUB.
        cl_ex = {'from': None, 'to': None}
        if salary:
            # fn_gr = lambda: 0.87 if vsal['gross'] else 1
            def fn_gr():
                return 0.87 if pages_req['salary']['gross'] else 1

            for i in cl_ex:
                if pages_req['salary'][i] is not None:
                    cl_ex[i] = int(
                        fn_gr() * salary[i] / exc[salary['currency']]
                    )

        # Create pages tuple
        pages_arr = (
            el,
            pages_req['employer']['name'],
            pages_req['name'],
            salary is not None,
            cl_ex['from'],
            cl_ex['to'],
            pages_req['experience']['name'],
            pages_req['schedule']['name'],
            [el['name'] for el in pages_req['key_skills']],
            clean_tags(pages_req['description']),
        )
        ret_lst.append(pages_arr)
    return ret_lst


def prepare_df(dct_df):
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
        df[df['Salary']][['Employer', 'From', 'To', 'Experience']][0:10]
    )
    # Save to file
    df.to_csv(r'hh_data.csv', index=False)


if __name__ == "__main__":
    print('Run hh.ru analysis...')
    ex_cur = get_exchange(EX_URL)
    id_list = get_list_id()
    print('Collect data from JSON. Create list of vacancies...')
    vac_list = get_vacancies(ids=id_list, exc=ex_cur)
    print('Prepare data frame...')
    prepare_df(vac_list)
    print('Done. Exit()')

# TODO: From / To list function. Average salary. Currency: convert to RUR.
