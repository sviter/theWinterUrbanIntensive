import requests
from bs4 import BeautifulSoup
import pandas as pd

dt = '2021-02-13'
bus_id = '00086262'

page = requests.get('https://www.bustime.ru/nizhniy-novgorod/transport/%s/%s/#time=03:00' % (dt, bus_id))
soup = BeautifulSoup(page.text, "lxml")
rawJ = soup.find_all('script')
J = str(rawJ[3])
J1 = J.split('var track = ')
J2 = J1[1].split('var time=')
track = J2[0].replace("'", '"')
str_list = [line.split('}') for line in track.split('{')]
a = [dot[0].split(',\n') for dot in str_list[1:]]
for dot in a:
    for row in range(len(dot)):
        dot[row] = dot[row].split(':', 1)[1].replace('"', '').replace('parseFloat(', '').replace('.replace(,,.) )',
                                                                                                 '').replace('\n',
                                                                                                             '')
df = pd.DataFrame(a)
df.to_csv('%s.csv' % dt, sep=';', index=False, mode='a',
          header=['uniqueid', 'gosnum', 'bortnum', 'timestamp', 'bus_id', 'heading', 'speed', 'lon', 'lat',
                  'direction'], encoding='utf-8-sig')

id_to_csv(dt, bus_id)