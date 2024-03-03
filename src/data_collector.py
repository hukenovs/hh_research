r"""Vacancy finder

------------------------------------------------------------------------

GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (c) 2020 Kapitanov Alexander

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

# Authors       : Alexander Kapitanov
# ...
# Contacts      : <empty>
# License       : GNU GENERAL PUBLIC LICENSE

import hashlib
import os
import pickle
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional
from urllib.parse import urlencode

import requests
from tqdm import tqdm

CACHE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "cache")


class DataCollector:
    r"""Researcher parameters

    Parameters
    ----------
    exchange_rates : dict
        Dict of exchange rates: RUR, USD, EUR.

    """
    __API_BASE_URL = "https://api.hh.ru/vacancies/"
    __DICT_KEYS = (
        "Ids",
        "Employer",
        "Name",
        "Salary",
        "From",
        "To",
        "Experience",
        "Schedule",
        "Keys",
        "Description",
    )

    def __init__(self, exchange_rates: Optional[Dict]):
        self._rates = exchange_rates

    @staticmethod
    def clean_tags(html_text: str) -> str:
        """Remove HTML tags from the string

        Parameters
        ----------
        html_text: str
            Input string with tags

        Returns
        -------
        result: string
            Clean text without HTML tags

        """
        pattern = re.compile("<.*?>")
        return re.sub(pattern, "", html_text)

    @staticmethod
    def __convert_gross(is_gross: bool) -> float:
        return 0.87 if is_gross else 1

    def get_vacancy(self, vacancy_id: str):
        # Get data from URL
        url = f"{self.__API_BASE_URL}{vacancy_id}"
        vacancy = requests.get(url).json()

        # Extract salary
        salary = vacancy.get("salary")

        # Calculate salary:
        # Get salary into {RUB, USD, EUR} with {Gross} parameter and
        # return a new salary in RUB.
        from_to = {"from": None, "to": None}
        if salary:
            is_gross = vacancy["salary"].get("gross")
            for k, v in from_to.items():
                if vacancy["salary"][k] is not None:
                    _value = self.__convert_gross(is_gross)
                    from_to[k] = int(_value * salary[k] / self._rates[salary["currency"]])

        # Create pages tuple
        return (
            vacancy_id,
            vacancy.get("name", ""),
            vacancy.get("employer", {}).get("name", ""),
            salary is not None,
            from_to["from"],
            from_to["to"],
            vacancy.get("experience", {}).get("name", ""),
            vacancy.get("schedule", {}).get("name", ""),
            [el["name"] for el in vacancy.get("key_skills", [])],
            self.clean_tags(vacancy.get("description", "")),
        )

    @staticmethod
    def __encode_query_for_url(query: Optional[Dict]) -> str:
        if 'professional_roles' in query:
            query_copy = query.copy()

            roles = '&'.join([f'professional_role={r}' for r in query_copy.pop('professional_roles')])

            return roles + (f'&{urlencode(query_copy)}' if len(query_copy) > 0 else '')

        return urlencode(query)

    def collect_vacancies(self, query: Optional[Dict], refresh: bool = False, num_workers: int = 1) -> Dict:
        """Parse vacancy JSON: get vacancy name, salary, experience etc.

        Parameters
        ----------
        query : dict
            Search query params for GET requests.
        refresh :  bool
            Refresh cached data
        num_workers :  int
            Number of workers for threading.

        Returns
        -------
        dict
            Dict of useful arguments from vacancies

        """
        if num_workers is None or num_workers < 1:
            num_workers = 1

        url_params = self.__encode_query_for_url(query)

        # Get cached data if exists...
        cache_name: str = url_params
        cache_hash = hashlib.md5(cache_name.encode()).hexdigest()
        cache_file = os.path.join(CACHE_DIR, cache_hash)
        try:
            if not refresh:
                print(f"[INFO]: Get results from cache! Enable refresh option to update results.")
                return pickle.load(open(cache_file, "rb"))
        except (FileNotFoundError, pickle.UnpicklingError):
            pass

        # Check number of pages...
        target_url = self.__API_BASE_URL + "?" + url_params
        num_pages = requests.get(target_url).json()["pages"]

        # Collect vacancy IDs...
        ids = []
        for idx in range(num_pages + 1):
            response = requests.get(target_url, {"page": idx})
            data = response.json()
            if "items" not in data:
                break
            ids.extend(x["id"] for x in data["items"])

        # Collect vacancies...
        jobs_list = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            for vacancy in tqdm(
                executor.map(self.get_vacancy, ids),
                desc="Get data via HH API",
                ncols=100,
                total=len(ids),
            ):
                jobs_list.append(vacancy)

        unzipped_list = list(zip(*jobs_list))

        result = {}
        for idx, key in enumerate(self.__DICT_KEYS):
            result[key] = unzipped_list[idx]

        pickle.dump(result, open(cache_file, "wb"))
        return result


if __name__ == "__main__":
    dc = DataCollector(exchange_rates={"USD": 0.01264, "EUR": 0.01083, "RUR": 1.00000})

    vacancies = dc.collect_vacancies(
        query={"text": "FPGA", "area": 1, "per_page": 50},
        # refresh=True
    )
    print(vacancies["Employer"])
