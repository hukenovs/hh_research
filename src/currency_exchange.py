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
import requests


def update_exchange_rates(target_url: str, currency: tuple) -> dict:
    """Parse exchange rates for RUB, USD, EUR and save them to `exchange_rates`

    Parameters
    ----------
    target_url : str
        URL to free exchange rates API
    currency : tuple
        List of currencies. For example: ["RUB", "USD", "EUR", "UAH"]

    Returns
    -------
    dict
        Dict of rates:

    """
    exchange_rates = dict()
    try:
        response = requests.get(target_url)
        rates = response.json()["rates"]
    except requests.exceptions.SSLError:
        raise AssertionError("[FAIL] Cannot get exchange rate! Try later or change the host API")
        # exit("[INFO] Exit from script. Cannot get data from URL!")

    for curr in currency:
        exchange_rates[curr] = rates[curr]

    # Change 'RUB' to 'RUR'
    exchange_rates["RUR"] = exchange_rates.pop("RUB")
    return exchange_rates


if __name__ == "__main__":
    _rates = update_exchange_rates(
        target_url="https://api.exchangerate-api.com/v4/latest/RUB", currency=("RUB", "USD", "EUR", "UAH"),
    )
    for k, v in _rates.items():
        print(f"{k}: {v :.05f}")
