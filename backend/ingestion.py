import pandas as pd

file_path = "data/raw/transactions.csv"

data = pd.read_csv(file_path)

print(data)