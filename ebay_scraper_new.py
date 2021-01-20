import csv
import requests
import bs4
import argparse
import re

from urllib.parse import quote_plus
from datetime import datetime, timedelta

# Widly used regexes compiled
re_html_cleanr = re.compile(r'<.*?>')
re_par         = re.compile(r'\(([^\)]*)\)')
re_percent     = re.compile(r'([0-9.]*)%')
re_date_f1     = re.compile(r'[A-z][a-z][a-z]-[0-3][0-9]-[0-2][0-9]')
re_date_f2     = re.compile(r'[0-3]?[0-9] [A-z][a-z][a-z] [1-2][09][0-9][0-9] at [1-2]?[0-9]')

# enter multiple phrases separated by '',
phrases =['samsung a7']

def clean_html(raw_html):    
    cleantext = re.sub(re_html_cleanr, '', raw_html)
    return cleantext

def get_in_paranthasis(str_par):
    return re_par.search(str_par)[1]

def get_percent(str_per):
    return re_percent.search(str_per)[1]
    
def get_date_f1(str_date):
    date_data = re_date_f1.search(str_date)[0]
    return datetime.strptime(date_data, '%b-%d-%y')

def get_date_f2(str_date):
    date_data = re_date_f2.search(str_date)[0]
    return datetime.strptime(date_data, '%d %b %Y at %H')

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

    user_hist = str( soup.find(**{'data-test-id':"user-history"}).contents[0] )
    member_since = (get_date_f1( user_hist ))
    print ("member_since", member_since)

    member_from = user_hist.split(" in ")[1]
    print ("member_from", member_from)

    return (rating, all_votes, positive_feedback, member_since, member_from)

def extract_seller_data(soup):
    seller_span = soup.find(class_='mbg-l')
    if seller_span:
        return get_data_from_seller_page(seller_span)

    seller_span = soup.find(class_='bdg-90')
    if seller_span:
        return get_data_from_seller_page(seller_span)

def get_bidding_price(soup):
    bid_price_element = soup.find(id='prcIsum_bidPrice')
    if (bid_price_element):
        return bid_price_element.getText()
    bid_price_element = soup.find(class_='vi-VR-cvipPrice')
    return bid_price_element.getText()

def get_bid_data_from_bid_page(href, opening_bid):
    res = requests.get(href)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, "lxml")

    winning_bid = None
    rows = soup.find(class_="ui-component-table_wrapper").contents[1]
    if (len(rows) > 1):
        opening_bid = rows.contents[-1].contents[1].getText()
        winning_bid = rows.contents[0].contents[1].getText()

    date_ended = get_date_f2( soup.find(class_="app-bid-info_wrapper").contents[0].contents[2].getText() )
    duration_txt = soup.find(class_="app-bid-info_wrapper").contents[0].contents[3].getText()
    duration = int( 
        duration_txt.split(':')[1].split(' ')[0]
    )
    
    date_started = date_ended - timedelta(days=duration)
    print ("date_started", date_started)
    print ("date_ended", date_ended)
    print ("duration", duration)
    return (opening_bid, winning_bid, date_started, date_ended, duration)

def extract_bid_data(soup):
    sold = 1
    bids_link = soup.find(id='vi-VR-bid-lnk')
    number_of_bids = bids_link.contents[0].contents[0]
    if number_of_bids == '0':
        sold = 0

    starting_bid_price = get_bidding_price(soup)
    winning_bid_price = None
    starting_bid_price, winning_bid_price, date_started, date_ended, duration = get_bid_data_from_bid_page(bids_link['href'], starting_bid_price)

    print ("starting_bid_price", starting_bid_price)
    print ("winning_bid_price", winning_bid_price)
    if starting_bid_price.startswith ('$'):
        starting_bid_price = starting_bid_price.replace('$', 'US ')

    if starting_bid_price.startswith ('US $'):
        starting_bid_price = starting_bid_price.replace('US $', 'US ')
    
    starting_bid_price_currancy, starting_bid_price_value = starting_bid_price.split(' ')
    winning_bid_price_currancy, winning_bid_price_value = (None, None)
    if winning_bid_price:
        winning_bid_price_currancy, winning_bid_price_value = winning_bid_price.split(' ')

        if winning_bid_price.startswith ('$'):
            winning_bid_price = winning_bid_price.replace('$', 'US ')

        if winning_bid_price.startswith ('US $'):
            winning_bid_price = winning_bid_price.replace('US $', 'US ')
    
    print ("starting_bid", starting_bid_price_currancy, starting_bid_price_value)
    print ("winning_bid", winning_bid_price_currancy, winning_bid_price_value)
    print ("Did the listing sell? ", sold)
    
    return (sold, date_started, date_ended, duration,
        starting_bid_price_currancy, starting_bid_price_value, 
        winning_bid_price_currancy, winning_bid_price_value, )

def get_original_link_soup(soup):
    original_link = soup.find(class_='nodestar-item-card-details__view-link')
    if original_link:
        res = requests.get(original_link['href'])
        res.raise_for_status()
        return bs4.BeautifulSoup(res.text, "lxml")
    
    original_link = soup.find(class_='vi-original-listing')
    if original_link:
        res = requests.get(original_link.contents[0]['href'])
        res.raise_for_status()
        return bs4.BeautifulSoup(res.text, "lxml")

    return soup

def explore_product_page(href):
    res = requests.get(href)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, "lxml")
    
    # if theres original link use it to get data
    soup = get_original_link_soup(soup)

    item_condition = soup.find(id="vi-itm-cond").getText()
    print ("item_condition", item_condition)
    
    item_location = soup.find(itemprop="availableAtOrFrom").getText().split(', ')[-1]
    print ("item_location", item_location)

    # (sold, date_started, date_ended, duration,
    #     starting_bid_price_currancy, starting_bid_price_value, 
    #     winning_bid_price_currancy, winning_bid_price_value, ) = extract_bid_data(soup)
    # (rating, all_votes, positive_feedback, member_since, member_from) = extract_seller_data(soup)

    # return (rating, all_votes, positive_feedback, member_since, member_from)

for phrase in phrases:
    site = ('https://www.ebay.com/sch/i.html?_from=R40&_sacat=0&_udlo=' +
            '&_udhi=&LH_Auction=1&_samilow=&_samihi=&_sadis=15&_stpos=90278-4805'+
            '&_fosrp=1&LH_Complete=1&_nkw={}'+
            '&_pppn=r1&scp=ce0').format(quote_plus(phrase))

    res = requests.get(site)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, "lxml")

    # grab all the links and store its href destinations in a list
    link_listing = soup.find_all(class_="vip")

    for i, l in enumerate(link_listing):
        title = l.contents[0]
        href = l['href']

        try:
            explore_product_page(href)
        except:
            print (href)
            raise

        # early break
        if i > 10:
            break


