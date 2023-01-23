import pandas as pd
import json

# Приклад читання збереженого контексту
obj = pd.read_pickle(r'data.pickle')
print(json.dumps(obj, indent=4, default=str))
