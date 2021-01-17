import csv
import requests
import bs4
import argparse
from urllib.parse import quote_plus
import re

# Widly used regexes compiled
re_html_cleanr = re.compile(r'<.*?>')
re_par         = re.compile(r'\(([^\)]*)\)')
re_percent     = re.compile(r'([0-9.]*)%')

# enter multiple phrases separated by '',
phrases =['samsung a7']

def clean_html(raw_html):    
    cleantext = re.sub(re_html_cleanr, '', raw_html)
    return cleantext

def get_in_paranthasis(str_par):
    return re_par.search(str_par)[1]

def get_percent(str_per):
    return re_percent.search(str_per)[1]
    
def get_seller_info_from_persona(seller_persona_span):
    print ("Num remarks:", get_in_paranthasis(clean_html( str(seller_persona_span.contents[1]) )))
    print ("precent: ", get_percent(str( seller_persona_span.contents[2] )))
    return

def get_data_from_seller_page(seller_span):
    seller_page_href = seller_span.contents[1]['href']
    res = requests.get(seller_page_href)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, "lxml")
    
    rating = soup.find(**{'data-test-id':"user-score"}).contents[0]
    print ("rating_score:", rating)

    all_votes = 0

    for i in range(3):
        all_votes += int( clean_html( str(soup.find(class_='overall-rating-summary').
            contents[1].contents[1].contents[i].contents[3] # table->tbody->line-i->cell-4 (count for 12 month)
    ) ) )
    print ("overall_votes:", all_votes)

    positive_feedback = float(get_percent( str(soup.find(class_='positiveFeedbackText')) ))
    print ("positive_feedback: {:.2f}".format(positive_feedback))


    return (rating, all_votes, positive_feedback)

def explore_product_page(href):
    res = requests.get(href)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, "lxml")

    # if theres original link use it to get data
    original_link = soup.find(class_='nodestar-item-card-details__view-link')
    if original_link:
        res = requests.get(original_link['href'])
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, "lxml")

    seller_span = soup.find(class_='mbg-l')
    if seller_span:
        return get_data_from_seller_page(seller_span)

    seller_span = soup.find(class_='bdg-90')
    if seller_span:
        return get_data_from_seller_page(seller_span)
        
for phrase in phrases:
    site = ('https://www.ebay.com/sch/i.html?_from=R40&_sacat=0&_udlo=' +
            '&_udhi=&LH_Auction=1&_samilow=&_samihi=&_sadis=15&_stpos=90278-4805'+
            '&_fosrp=1&LH_Complete=1&_nkw={}'+
            '&_pppn=r1&scp=ce0').format(quote_plus(phrase))

    res = requests.get(site)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, "lxml")

    # grab all the links and store its href destinations in a list
    link_objs = soup.find_all(class_="vip")

    title_quote = re.compile('[^0-9A-Za-z .-_]')
    for i, l in enumerate(link_objs):
        title = l.contents[0]
        href = l['href']

        try:
            explore_product_page(href)
        except:
            print (href)
            raise

    if i > 10:
        break


