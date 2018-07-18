import pandas as pd
from bs4 import BeautifulSoup
import urllib2
import Claim as claim_obj
import dateparser


ignore_urls = []

def get_all_claims(criteria):
    claims = []


    soup = get_soup('http://www.e-farsas.com/')

    # Number of pages
    number_of_pages = 136

    # For each page
    for page_i in range(number_of_pages):
        if (criteria.maxClaims > 0 and len(claims)>= criteria.maxClaims):
            break
        page_i += 1
        print('Page ' + str(page_i) + '|' + str(number_of_pages))
        try:
            soup = get_soup('http://www.e-farsas.com/page/' + str(page_i))

            fact_links = [fl.find('a')['href'] for fl in soup.findAll('li', {"class": "infinite-post"})]
            for f_link in fact_links:
                if f_link in ignore_urls:
                    continue
                if (criteria.maxClaims > 0 and len(claims) >= criteria.maxClaims):
                    break
                print(f_link)
                soup2 = get_soup(f_link)
                title_ = soup2.find('h1').text

                tags_ = [t.text for t in soup2.findAll('a', {'rel': 'tag'})]

                date_ = soup2.find('span', {'class': 'post-date'}).text
                claim_ = new_claim(f_link, date_, title_, tags_)
                if (criteria.html):
                    claim_.setHtml(soup2.prettify("utf-8"))
                refered_links = [l['href'] for l in soup2.find('section', {'id': 'mvp-content-main'}).findAll('a')]
                claim_.setRefered_links(refered_links)
                claim_.setClaim(soup2.find('strong').text)
                claim_.setBody("\n".join([l.text for l in soup2.find('section', {'id': 'mvp-content-main'}).findAll('p')]))
                claims.append(claim_.getDict())
        except:
            print "error=>"+str('http://www.e-farsas.com/page/' + str(page_i))
    print('Number of claims: '+str(len(claims)))
    pdf = pd.DataFrame(claims)
    return pdf


def get_soup(url):
    user_agent = 'Mozilla/5.0'
    request = urllib2.urlopen(urllib2.Request(url, data=None, headers={'User-Agent': user_agent}))
    page = request.read()
    return BeautifulSoup(page, 'lxml')


def new_claim(f_link, date, title, tags):
    claim_ = claim_obj.Claim()
    claim_.setUrl(f_link)
    claim_.setTitle(title)
    claim_.setTags(tags)
    date_ = date.strip().split()
    date_ = "-".join([date_[4], date_[2], date_[0]])
    claim_.setDate(dateparser.parse(date_).strftime("%Y-%m-%d"))
    claim_.setSource("efarsas")
    claim_.setBody("")
    return claim_
