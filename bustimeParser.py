import argparse
from datetime import datetime
import os
import requests
import lxml
from bs4 import BeautifulSoup
import re
import time
import pandas as pd

parser = argparse.ArgumentParser(description='Собирает с bustime.ru информацию об автобусах и их координатах за определённый день. Пакует в csv.')
parser.add_argument('--city', required=True, help='Город в формате bustime. Например, "nizhniy-novgorod"')
parser.add_argument('--date', help='Дата в формате гггг-мм-дд. Если не указана, берётся вчерашняя дата.')
parser.add_argument('--out-folder', required=True,
                      help='Путь до папки, в которую складывать итоговый csv')
options = parser.parse_args()

city = options.city
dt = options.date
if not dt:
    dt = (datetime.now() - imedelta(days=1)).strftime('%Y-%m-%d')

if not os.path.exists(options.out_folder):
    os.makedirs(options.out_folder)
out_file_path = os.path.join(options.out_folder, '%s.csv' % dt)

start_time = time.time()
base_url = 'https://www.bustime.ru'

bus_id = 0  # 8013
rex_head = re.compile(r'\/%s\/transport\/%s\/(\S*)\/' % (city, dt), flags=0)
rex_page = re.compile(r'\/%s\/transport\/%s\/page-(\d*)' % (city, dt), flags=0)
# r = '<div class="ui grid" style="margin-top:1em"><div class="column"><div class="ui pagination right menu"><a class="active item" href="/nizhniy-novgorod/transport/2021-01-21/page-1">1</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-2">2</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-3">3</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-4">4</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-5">5</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-6">6</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-7">7</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-8">8</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-9">9</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-10">10</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-11">11</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-12">12</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-13">13</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-14">14</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-15">15</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-16">16</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-17">17</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-18">18</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-19">19</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-20">20</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-21">21</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-22">22</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-23">23</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-24">24</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-25">25</a><a class="item" href="/nizhniy-novgorod/transport/2021-01-21/page-26">26</a></div></div></div>'

# марштуты в этот день
"""
m = soup.find('select', {'name': 'bus_id'})
#print(m, type(m))
with open('select.txt', 'w') as output_file:
    for opt in m:
        if opt['value'] != "0":
            output_file.write(opt['value']+'\t'+opt.text+'\n')
"""


def get_html(url):
    page = ""
    while page == '':
        try:
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36'}
            page = requests.get(url, headers=headers)
            return page.text
        except:
            print("Connection refused by the server..")
            print("Let me sleep for 10 seconds")
            time.sleep(10)


def soup2head(s, p):
    spans = s.find_all('span', {'id': 'head'})
    res = []
    for span in spans:
        a = span.find('a')
        res.append({'id': rex_head.search(a.get('href'))[1], 'reg_num': a.text.strip(), 'page': p})
    return res


# .pagination
heads = []
url = '%s/%s/transport/%s/' % (base_url, city, dt)
soup = BeautifulSoup(get_html(url), "lxml")
pages = soup.find('div', {'class': 'ui pagination right menu'}).find_all('a')
if pages is not None:
    # print(pages[0].get('href'))
    # print(pages.prettify())
    # сэкономим на том, что первая уже загружена
    heads = heads + soup2head(soup, '1')
    for a in pages[1:]:
        page = a.get('href')
        url = base_url + page
        soup = BeautifulSoup(get_html(url), "lxml")
        heads = heads + soup2head(soup, rex_page.search(page)[1])
        print(url)

    for head in heads:
        page = requests.get('https://www.bustime.ru/nizhniy-novgorod/transport/%s/%s/#time=03:00' % (dt, head['id']))
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
        df.to_csv(out_file_path, sep=';', index=False, mode='a',
                  header=False, encoding='utf-8-sig')
    # if 1 == len(pages):
    #     print(pages[0].get('href'))
    # else:
    with open('heads.txt', 'w') as fout:
        fout.write('page\tid\treg_num\n')
        for head in heads:
            # print(head)
            fout.write(head['page'] + '\t' + head['id'] + '\t' + head['reg_num'] + '\n')
    print(len(heads))

print("--- %s seconds ---" % (time.time() - start_time))
