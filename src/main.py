import requests
from bs4 import BeautifulSoup
response = requests.get('https://www.mariettaga.gov/AgendaCenter')

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
