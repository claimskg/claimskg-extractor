import pandas as pd
from bs4 import BeautifulSoup
import urllib2
import Claim as claim_obj
import dateparser


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
        if (criteria.maxClaims > 0 and len(claims)>= criteria.maxClaims):
            break
        page_i += 1
        print('Page ' + str(page_i) + '|' + str(number_of_pages))
        soup = get_soup('https://apublica.org/checagem/page/' + str(page_i) + '/')

        fact_links = [fl.a['href'] for fl in soup.findAll('div', {"class": "card"})]
        for f_link in fact_links:
            if f_link in ignore_urls:
                continue
            if (criteria.maxClaims > 0 and len(claims)>= criteria.maxClaims):
                break
            print(f_link)
            soup2 = get_soup(f_link)
            title_ = soup2.find('title').text
            # claims_ = [claim.text for claim in soup2.find_all('strong') if u'\u201c' in claim.text]
            # credibilities_ = [l['alt'] for l in soup2.find_all('img', {'class': 'alignleft'}) if '-400.jpg' in l['src']]
            # url_ = f_link

            contr = 0
            refered_links = []
            date_ = soup2.find('span', {'class': 'date'}).text
            claim_ = new_claim(f_link, date_, title_)
            stop = False
            for c in soup2.find('div', {'class', 'post-contents'}).contents:
                if c.name is None: continue
                if c.name == 'hr':
                    if stop:
                        claim_.setRefered_links(refered_links)
                        claims.append(claim_.getDict())
                        claim_ = new_claim(f_link, date_, title_)
                        stop = False
                    contr = 1
                    continue
                if contr == 1:
                    claim_.setClaim(c.text)
                    contr = 2
                    if c.find('img'):
                        claim_.setConclusion(c.img['alt'])
                        contr = 3
                    stop = True
                    continue
                if contr == 2:
                    claim_.setConclusion(c.img['alt'])
                    claim_.setBody(claim_.body + "\n" + c.text)
                    for l in c.findAll('a', href=True):
                        refered_links.append(l['href'])
                    contr = 3
                    continue
                if contr == 3:
                    for l in c.findAll('a', href=True):
                        refered_links.append(l['href'])
                    claim_.setBody(claim_.body + "\n" + c.text)
                    for l in c.findAll('a', href=True):
                        refered_links.append(l['href'])
            if stop:
                claim_.setRefered_links(refered_links)
                claims.append(claim_.getDict())
    print('Number of claims: '+str(len(claims)))
    pdf = pd.DataFrame(claims)
    return pdf


def get_soup(url):
    user_agent = 'Mozilla/5.0'
    request = urllib2.urlopen(urllib2.Request(url, data=None, headers={'User-Agent': user_agent}))
    page = request.read()
    return BeautifulSoup(page, 'lxml')


def new_claim(f_link, date, title):
    claim_ = claim_obj.Claim()
    claim_.setUrl(f_link)
    claim_.setTitle(title)
    date_ = date.strip().split()
    date_ = "-".join([date_[4], date_[2], date_[0]])
    claim_.setDate(dateparser.parse(date_).strftime("%Y-%m-%d"))
    claim_.setSource("publica")
    claim_.setBody("")
    return claim_
