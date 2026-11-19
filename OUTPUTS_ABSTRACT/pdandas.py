import pandas as pd

data = {
    'Nom': ['Alice', 'Bob', 'Charlie', 'David'],
    'Âge': [25, 30, 35, 40],
    'Ville': ['Paris', 'Lyon', 'Marseille', 'Nice']
}

df = pd.DataFrame(data, index=['a', 'b', 'c', 'd'])
print(df)
df.loc["a":"b","Nom":"Ville"]