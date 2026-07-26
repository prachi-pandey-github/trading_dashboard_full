# replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key

import requests


url = 'https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY_ADJUSTED&symbol=IBM&apikey=DZHFIAI5MXVWLKRT'
r = requests.get(url)
data = r.json()

print(data)