import pandas as pd


class TabularParser:

    @staticmethod
    def parse_csv(file_path):

        df = pd.read_csv(file_path)

        return df.to_string(index=False)

    @staticmethod
    def parse_excel(file_path):

        df = pd.read_excel(file_path)

        return df.to_string(index=False)