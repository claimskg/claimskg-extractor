import pandas as pd
from bs4 import BeautifulSoup
import urllib2


def get_all_claims(criteria):
    claims = []

    url = 'https://apublica.org/checagem/'
    user_agent = 'Mozilla/5.0'
    request = urllib2.urlopen(urllib2.Request(url, data=None, headers={'User-Agent': user_agent}))
    page = request.read()
    soup = BeautifulSoup(page, 'lxml')

    # Get the number of pages
    pages_links = soup.findAll('a', {"class": "page-link"})
    number_of_pages = int(pages_links[::-1][1].text)
    print('Number of pages: ' + str(number_of_pages))

    # For each page
    for page_i in range(number_of_pages):
        page_i += 1
        print('Page ' + str(page_i) + '|' + str(number_of_pages))
        url = 'https://apublica.org/checagem/page/' + str(page_i) + '/'
        print(url)
        user_agent = 'Mozilla/5.0'
        request = urllib2.urlopen(urllib2.Request(url, data=None, headers={'User-Agent': user_agent}))
        page = request.read()
        soup = BeautifulSoup(page, 'lxml')
        fact_links = [fl.a['href'] for fl in soup.findAll('div', {"class": "card"})]
        for fact in fact_links:
            print(fact)



    pdf = pd.DataFrame(claims)
    return pdf
