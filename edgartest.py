# edgartest.py
# a program to try to pull requested financial data from SEC documents

import requests
import datetime
from bs4 import BeautifulSoup
import re
import xml.etree.ElementTree as ET


# establish what we want to pull
CIK = "gpx"
type = "10-Q"
today = datetime.date.today()
dateb = today.strftime("%Y%m%d")
action = "getcompany"
count = 1

# set up a data requested
data_request = "us-gaap:Revenues"

# construct the target URL
target_url = "https://www.sec.gov/cgi-bin/browse-edgar?action={}&CIK={}&type={}&dateb={}&count={}"
edgar_page = requests.get(target_url.format(action,CIK,type,dateb,count))

# parse the page to find the xml links we want.
edgar_tree = BeautifulSoup(edgar_page.text, 'lxml')


# create a holder for all the xml_links
xml_links = []

# traverse the edgar_page to find all the xml links
table_tag = edgar_tree.find('table', class_='tableFile2', summary='Results')
rows = table_tag.find_all('tr')
for row in rows:
    cells = row.find_all('td')
    if len(cells) >= 2:
        if cells[0].text.find(type) != -1:
            xml_links.append('https://www.sec.gov' + cells[1].a['href'])


# Now we have to go to each page and find the correct INS file.

# create a bin for the xmmls
xml_urls = []

for link in xml_links:
    page = requests.get(link)
    tree = BeautifulSoup(page.text, 'lxml')
    table_tag = tree.find('table', class_='tableFile', summary="Data Files")
    rows = table_tag.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 3:
            if cells[3].text.find("INS") != -1:
                xml_urls.append('https://www.sec.gov/' + cells[2].a['href'])


# now we have the filenames of the xmls we want.
# so have to load and parse each one.
xml_trees = []
for link in xml_urls:
    page_text = requests.get(link).text
    xml_trees.append(ET.fromstring(page_text))


# go through the trees looking for what we want.
for i in range (count):
    iter_ = xml_trees[i].getiterator()
    for elem in iter_:
        if re.search("RevenueFrom", elem.tag):
            print(elem.tag, elem.attrib["contextRef"], elem.text)




