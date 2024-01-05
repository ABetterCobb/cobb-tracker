import requests
import pickle
import time

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    )

session = requests.Session()
with open('cookies.pkl', 'rb') as f:
    session.cookies.update(pickle.load(f))
file_page = session.get("https://records.smyrnaga.gov/WebLink/DocView.aspx?id=5483&dbid=0&repo=CityofSmyrna", headers={"User-Agent": USER_AGENT})
gen = session.post('https://records.smyrnaga.gov/WebLink/GeneratePDF10.aspx?key=5483&PageRange=1-14&Watermark=0')
print(gen.text)

#print(file_page.text)
the_id = gen.text.partition('\n')[0].strip()
dictionary = { "Key" : the_id }
print(f"https://records.smyrnaga.gov/WebLink/PDF10/{the_id}/5483")
time.sleep(4)
file = session.get(f"https://records.smyrnaga.gov/WebLink/PDF10/{the_id}/5483")
print(file.content)

with open('dexter.pdf', 'wb') as file2:
    file2.write(file.content)
