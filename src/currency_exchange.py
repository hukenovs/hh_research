"""Get currency exchange for RUB, EUR, USD from remore server

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
import json
from typing import Dict

import requests


class Exchanger:
    __EXCHANGE_URL = "https://api.exchangerate-api.com/v4/latest/RUB"

    def __init__(self, config_path: str):
        self.config_path = config_path

    def update_exchange_rates(self, rates: Dict):
        """Parse exchange rates for RUB, USD, EUR and save them to `rates`

        Parameters
        ----------
        rates : dict
            Dict of currencies. For example: {"RUB": 1, "USD": 0.001}
        """

        try:
            response = requests.get(self.__EXCHANGE_URL)
            new_rates = response.json()["rates"]
        except requests.exceptions.SSLError:
            raise AssertionError("[FAIL] Cannot get exchange rate! Try later or change the host API")

        for curr in rates:
            rates[curr] = new_rates[curr]

        # Change 'RUB' to 'RUR'
        rates["RUR"] = rates.pop("RUB")

    def save_rates(self, rates: Dict):
        """Save rates to JSON config."""

        with open(self.config_path, "r") as cfg:
            data = json.load(cfg)

        data["rates"] = rates

        with open(self.config_path, "w") as cfg:
            json.dump(data, cfg, indent=2)


if __name__ == "__main__":
    _exchanger = Exchanger("../settings.json")
    _default = {"RUB": None, "USD": None, "EUR": None, "UAH": None}
    _exchanger.update_exchange_rates(_default)
    _exchanger.save_rates(_default)
    for _k, _v in _default.items():
        print(f"{_k}: {_v :.05f}")
