import requests
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0'}
values = {"year": "2015", "catID": "7"}
session = requests.Session()
response = session.post('https://www.mariettaga.gov/AgendaCenter', headers=headers, data=values)

webpage = response.content
soup = BeautifulSoup(webpage, 'html.parser')
rows = soup.find(id="table7").tbody.find_all('tr')

for row in rows:
    date_header = row.find('td', class_=None)
    print(date_header.strong.get_text() + " " + date_header.p.get_text().strip())
    minutes = row.find('td', class_="minutes")
    minutes_link = minutes.find('a')

    if minutes_link:
        print('https://www.mariettaga.gov'+minutes_link.get('href'))
