import pandas as pd

class CleanFixtures:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def remove_nan(self):
        self.df = self.df[self.df['score_home'].notna() & self.df['score_away'].notna()]
        self.df["score_home"] = pd.to_numeric(self.df["score_home"], errors="coerce")
        self.df["score_away"] = pd.to_numeric(self.df["score_away"], errors="coerce")
        return self.df.dropna(subset=["score_home", "score_away"])
