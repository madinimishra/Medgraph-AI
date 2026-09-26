import os
import pandas as pd


class SyntheaImporter:

    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def load_csv(self, filename: str):

        path = os.path.join(
            self.data_dir,
            filename
        )

        if not os.path.exists(path):
            print(f"[WARNING] {filename} not found")
            return None

        print(f"[INFO] Loading {filename}")

        df = pd.read_csv(path)

        print(
            f"[INFO] {filename}: "
            f"{len(df)} rows"
        )

        return df

    def inspect(self):

        files = [
            "patients.csv",
            "encounters.csv",
            "conditions.csv",
            "medications.csv",
            "observations.csv",
            "procedures.csv",
            "allergies.csv",
            "careplans.csv",
            "immunizations.csv",
            "providers.csv",
            "organizations.csv",
        ]

        for filename in files:

            df = self.load_csv(filename)

            if df is None:
                continue

            print("\n" + "=" * 70)
            print(filename)
            print("=" * 70)

            print("Columns:")
            print(list(df.columns))

            print("\nFirst row:")

            print(
                df.head(1).to_dict(
                    orient="records"
                )
            )

            print()


if __name__ == "__main__":

    importer = SyntheaImporter(
        "data/synthea"
    )

    importer.inspect()