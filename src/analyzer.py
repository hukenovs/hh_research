r"""Researcher: collect statistics, predict salaries etc.

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

import re
from typing import Dict, List

import matplotlib.pyplot as plt
import nltk
import numpy as np
import pandas as pd
import seaborn as sns


class Analyzer:
    def __init__(self, save_csv: bool = False):
        self.save_csv = save_csv
        # try:
        #     nltk.download("stopwords")
        # except:
        #     print(r"[INFO] You have downloaded stopwords!")

    @staticmethod
    def find_top_words_from_keys(keys_list: List) -> pd.Series:
        """Find most used words into description of vacancies.

        Parameters
        ----------
        keys_list : list
            List of sentences from keywords of vacancies.

        Returns
        -------
        pd.Series
            List of sorted keywords.

        """
        # Create a list of keys for all vacancies
        lst_keys = []
        for keys_elem in keys_list:
            for el in keys_elem:
                if el != "":
                    lst_keys.append(re.sub("'", "", el.lower()))

        # Unique keys and their counter
        set_keys = set(lst_keys)
        # Dict: {Key: Count}
        dct_keys = {el: lst_keys.count(el) for el in set_keys}
        # Sorted dict
        srt_keys = dict(sorted(dct_keys.items(), key=lambda x: x[1], reverse=True))
        # Return pandas series
        return pd.Series(srt_keys, name="Keys")

    @staticmethod
    def find_top_words_from_description(desc_list: List) -> pd.Series:
        """Find most used words into description of vacancies.

        Parameters
        ----------
        desc_list : list
            List of sentences from vacancy description.

        Returns
        -------
        pd.Series
            List of sorted words from descriptions.

        """
        words_ls = " ".join([re.sub(" +", " ", re.sub(r"\d+", "", el.strip().lower())) for el in desc_list])
        # Find all words
        words_re = re.findall("[a-zA-Z]+", words_ls)
        # Filter words with length < 3
        words_l2 = [el for el in words_re if len(el) > 2]
        # Unique words
        words_st = set(words_l2)
        # Remove 'stop words'
        try:
            _ = nltk.corpus.stopwords.words("english")
        except LookupError:
            nltk.download("stopwords")
        finally:
            stop_words = set(nltk.corpus.stopwords.words("english"))

        # XOR for dictionary
        words_st ^= stop_words
        words_st ^= {"amp", "quot"}
        # Dictionary - {Word: Counter}
        words_cnt = {el: words_l2.count(el) for el in words_st}
        # Pandas series
        return pd.Series(dict(sorted(words_cnt.items(), key=lambda x: x[1], reverse=True)))

    def prepare_df(self, vacancies: Dict) -> pd.DataFrame:
        """Prepare data frame and save results

        Parameters
        ----------
        vacancies: dict
            Dict of parsed vacancies.

        """

        # Create pandas dataframe
        df = pd.DataFrame.from_dict(vacancies)
        # Print some info from data frame
        with pd.option_context("display.max_rows", None, "display.max_columns", None):
            print(df[df["Salary"]][["Employer", "From", "To", "Experience"]][0:15])
        # Save to file
        if self.save_csv:
            print("\n\n[INFO]: Save dataframe to file...")
            df.to_csv(rf"hh_results.csv", index=False)
        return df

    def analyze_df(self, df: pd.DataFrame):
        """Load data frame and analyze results

        """
        sns.set()
        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        print(df[df["Salary"]][0:7])

        print("\nNumber of vacancies: {}".format(df["Ids"].count()))
        print("\nVacancy with max salary: ")
        print(df.iloc[df[["From", "To"]].idxmax()])
        print("\nVacancy with min salary: ")
        print(df.iloc[df[["From", "To"]].idxmin()])

        print("\n[INFO]: Describe salary data frame")
        df_stat = df[["From", "To"]].describe().applymap(np.int32)
        print(df_stat.iloc[list(range(4)) + [-1]])

        print('\n[INFO]: Average statistics (filter for "From"-"To" parameters):')
        comb_ft = np.nanmean(df[df["Salary"]][["From", "To"]].to_numpy(), axis=1)
        print("Describe salary series:")
        print("Min    : %d" % np.min(comb_ft))
        print("Max    : %d" % np.max(comb_ft))
        print("Mean   : %d" % np.mean(comb_ft))
        print("Median : %d" % np.median(comb_ft))

        print("\nMost frequently used words [Keywords]:")
        most_keys = self.find_top_words_from_keys(df["Keys"].to_list())
        print(most_keys[:12])

        print("\nMost frequently used words [Description]:")
        most_words = self.find_top_words_from_description(df["Description"].to_list())
        print(most_words[:12])

        print("\n[INFO]: Plot results. Close figure box to continue...")
        fz = plt.figure("Salary plots", figsize=(12, 8))
        fz.add_subplot(2, 2, 1)
        plt.title("From / To: Boxplot")
        sns.boxplot(data=df[["From", "To"]].dropna() / 1000, width=0.4)
        plt.ylabel("Salary x 1000 [RUB]")
        fz.add_subplot(2, 2, 2)
        plt.title("From / To: Swarmplot")
        sns.swarmplot(data=df[["From", "To"]].dropna() / 1000, size=6)

        fz.add_subplot(2, 2, 3)
        plt.title("From: Distribution ")
        sns.histplot(df["From"].dropna() / 1000, bins=14, color="C0", kde=True)
        plt.grid(True)
        plt.xlabel("Salary x 1000 [RUB]")
        plt.xlim([-50, df["From"].max() / 1000])
        plt.yticks([], [])

        fz.add_subplot(2, 2, 4)
        plt.title("To: Distribution")
        sns.histplot(df["To"].dropna() / 1000, bins=14, color="C1", kde=True)
        plt.grid(True)
        plt.xlim([-50, df["To"].max() / 1000])
        plt.xlabel("Salary x 1000 [RUB]")
        plt.yticks([], [])
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    analyzer = Analyzer()
