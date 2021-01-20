import csv
import requests
import bs4
import argparse
import re
import math
from urllib.parse import quote_plus
from datetime import datetime

# Widly used regexes compiled
re_par         = re.compile(r'\(([^\)]*)\)')
re_percent     = re.compile(r'([0-9.]*)%')
re_date        = re.compile(r'[A-z][a-z][a-z]-[0-3][0-9]-[0-2][0-9]')

# enter multiple phrases separated by '',
phrases = ['samsung a7']


def get_total_pages(given_url):
  resp = requests.get(url)
  soup = bs4.BeautifulSoup(resp.text , 'html.parser')
  total_items = soup.find('h2' ,class_ = 'srp-controls__count-heading').string.split()[-2]
  # Page contain 48 items
  total_pages = math.floor(float(total_items.replace(',','')) / 48)
  return total_pages

def get_in_paranthasis(str_par):
    return re_par.search(str_par)[1]


def get_percent(str_per):
    return re_percent.search(str_per)[1]


def get_date(str_date):
    date_data = re_date.search(str_date)[0]
    return datetime.strptime(date_data, '%b-%d-%y')

def get_data_from_seller_page(seller_span):
    seller_page_href = seller_span.contents[1]['href']
    res = requests.get(seller_page_href)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, "html.parser")

    rating = soup.find(**{'data-test-id': "user-score"}).contents[0]
    print("rating_score:", rating)

    all_votes = 0

    for i in range(3):
        all_votes += int( (soup.find(class_='overall-rating-summary').
            contents[1].contents[1].contents[i].contents[3] # table->tbody->line-i->cell-4 (count for 12 month)
        ).getText() )
    print ("overall_votes:", all_votes)

    positive_feedback = float(get_percent(str(soup.find(class_='positiveFeedbackText'))))
    print("positive_feedback: {:.2f}".format(positive_feedback))

    user_hist = str(soup.find(**{'data-test-id': "user-history"}).contents[0])
    member_since = (get_date(user_hist))
    print("member_since", member_since)

    member_from = user_hist.split(" in ")[1]
    print("member_from", member_from)

    return (rating, all_votes, positive_feedback, member_since, member_from)


def explore_product_page(href):
    res = requests.get(href)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, "html.parser")

    # if theres original link use it to get data
    original_link = soup.find(class_='nodestar-item-card-details__view-link')
    if original_link:
        res = requests.get(original_link['href'])
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, "html.parser")

    seller_span = soup.find(class_='mbg-l')
    if seller_span:
        return get_data_from_seller_page(seller_span)

    seller_span = soup.find(class_='bdg-90')
    if seller_span:
        return get_data_from_seller_page(seller_span)


for phrase in phrases:
    site = ('https://www.ebay.com/sch/i.html?_from=R40&_sacat=0&_udlo=' +
            '&_udhi=&LH_Auction=1&_samilow=&_samihi=&_sadis=15&_stpos=90278-4805' +
            '&_fosrp=1&LH_Complete=1&_nkw={}' +
            '&_pppn=r1&scp=ce0').format(quote_plus(phrase))

    res = requests.get(site)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, "html.parser")
    url = 'https://il.ebay.com/b/Cell-Phones-Smartphones/9355/bn_320094?LH_Auction=1&LH_Complete=1&rt=nc&_dmd=1'
    pages = get_total_pages(url)
    for page in range(1, pages + 1):
        cur_page = f'{url}&_pgn={page}'
        print(cur_page)
        if page > 10:
            break

    # grab all the links and store its href destinations in a list
    page = soup.prettify()
    link_objs = soup.find_all(class_="vip")


    title_quote = re.compile('[^0-9A-Za-z .-_]')
    for i, l in enumerate(link_objs):
        title = l.contents[0]
        href = l['href']

        try:
            explore_product_page(href)
        except:
            print(href)
            raise

        if i > 10:
            break
