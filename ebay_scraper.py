import csv
import requests
import bs4
import argparse
from urllib.parse import quote_plus

# parser = argparse.ArgumentParser(description='Process a list of search terms.')
# parser.add_argument('terms', metavar='N', type=str, nargs='+',
#                    help='comma separated list of terms to search for')

# args = parser.parse_args()
# print args.accumulate(args.terms)

# enter multiple phrases separated by '',
phrases =['samsung a7']


for phrase in phrases:
    # site = 'https://www.ebay.com/sch/i.html?_from=R40&_sacat=0&_udlo=&_udhi=&LH_Auction=1&_samilow=&_samihi=&_sadis=15&_stpos=90278-4805&_fosrp=1&_sop=13&_dmd=1&_ipg=200&_nkw={}&LH_Complete=1&rt=nc&_trksid=p2045573.m1684'.format(quote_plus(phrase))
    site = 'https://www.ebay.com/sch/i.html?_from=R40&_sacat=0&_udlo=&_udhi=&LH_Auction=1&_samilow=&_samihi=&_sadis=15&_stpos=90278-4805&_fosrp=1&LH_Complete=1&_nkw={}&_pppn=r1&scp=ce0'.format(quote_plus(phrase))
    print (site)

    res = requests.get(site)
    res.raise_for_status()
    soup = bs4.BeautifulSoup(res.text, "lxml")

  
    # grab the date/time stamp of each auction listing
    dte = [e.span.contents[0].split(' ')[0] for e in soup.find_all(class_="tme")]

       # grab all the links and store its href destinations in a list
    titles = [e.contents[0] for e in soup.find_all(class_="vip")]
        
    # grab all the links and store its href destinations in a list
    links = [e['href'] for e in soup.find_all(class_="vip")]

    # grab all the bid spans and split its contents in order to get the number only
    bids = [e.span.contents[0].split(' ')[0] for e in soup.find_all("li", "lvformat")]

    # grab all the prices and store those in a list
    prices = [e.contents[0] for e in soup.find_all("span", "bold bidsold")]

    # zip each entry out of the lists we generated before in order to combine the entries
    # belonging to each other and write the zipped elements to a list
    l = [e for e in zip(dte, titles, links, prices, bids)]

    # write each entry of the rowlist `l` to the csv output file
    with open('%s.csv' % phrase, 'w') as csvfile:
        w = csv.writer(csvfile)
        for e in l:
            w.writerow(e)