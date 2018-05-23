import pandas as pd
from bs4 import BeautifulSoup
import urllib2


ignore_urls = ['https://apublica.org/2017/07/truco-7-fatos-sobre-a-reforma-trabalhista/',
               'https://apublica.org/checagem/',
               'https://apublica.org/2017/03/truco-6-fatos-sobre-a-reforma-da-previdencia/']

def get_all_claims(criteria):
    claims = []

    soup = get_soup('https://apublica.org/checagem/')

    # Get the number of pages
    pages_links = soup.findAll('a', {"class": "page-link"})
    number_of_pages = int(pages_links[::-1][1].text)
    print('Number of pages: ' + str(number_of_pages))

    # For each page
    for page_i in range(number_of_pages):
        page_i += 1
        print('Page ' + str(page_i) + '|' + str(number_of_pages))
        soup = get_soup('https://apublica.org/checagem/page/' + str(page_i) + '/')

        fact_links = [fl.a['href'] for fl in soup.findAll('div', {"class": "card"})]
        for f_link in fact_links:
            if f_link in ignore_urls:
                continue
            print(f_link)
            soup2 = get_soup(f_link)

            # claims_ = [claim.text for claim in soup2.find_all('strong') if u'\u201c' in claim.text]
            # credibilities_ = [l['alt'] for l in soup2.find_all('img', {'class': 'alignleft'}) if '-400.jpg' in l['src']]
            # url_ = f_link

            contr = 0
            claims_ = []
            claim_ = {'body': ""}
            stop = False
            for c in soup2.find('div', {'class', 'post-contents'}).contents:
                if c.name is None: continue
                #print(c.name)
                if c.name == 'hr':
                    if stop:
                        claims_.append(claim_)
                        claim_ = {'body': ""}
                        stop = False
                    contr = 1
                    continue
                if contr == 1:
                    claim_['claim'] = c.text
                    contr = 2
                    if c.find('img'):
                        claim_['credibility'] = c.img['alt']
                        contr = 3
                    stop = True
                    continue
                if contr == 2:
                    claim_['credibility'] = c.img['alt']
                    contr = 3
                    continue
                if contr == 3:
                    claim_['body'] += "\n" + c.text
            if stop:
                claims_.append(claim_)

    pdf = pd.DataFrame(claims)
    return pdf


def get_soup(url):
    user_agent = 'Mozilla/5.0'
    request = urllib2.urlopen(urllib2.Request(url, data=None, headers={'User-Agent': user_agent}))
    page = request.read()
    return BeautifulSoup(page, 'lxml')
