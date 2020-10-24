import datetime
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd
from bs4 import BeautifulSoup
from dateparser.search import search_dates

from claim_extractor import Claim


def get_all_claims(criteria):
    # performing a search by each letter, and adding each article to a urls_ var.
    now = datetime.datetime.now()
    urls_ = {}
    letters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "m", "o", "p", "q", "x", "y", "z"]
    letters = ["a"]
    for l in letters:
        for page in range(1, 500):
            if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
                break
            try:
                print(("http://www.mimikama.at/page/" + str(page) + "/?s=" + l))
                page = urllib.request.urlopen("http://www.mimikama.at/page/" + str(page) + "/?s=" + l).read()
            except:
                break
            soup = BeautifulSoup(page, "lxml")
            soup.prettify()
            links = soup.find('div', {"class": "td-ss-main-content"}).findAll('a', {"rel": "bookmark"}, href=True)
            if len(links) != 0:
                for anchor in links:
                    if (anchor['href'] not in list(urls_.keys())):
                        urls_[anchor['href']] = l
                        print("adding " + str(anchor['href']))
                        if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
                            break
            else:
                print("break!")
                break

    claims = []
    index = 0
    # visiting each article's dictionary and extract the content.
    for url in list(urls_.keys()):
        try:
            print(str(index) + "/" + str(len(list(urls_.keys()))) + " extracting " + str(url))
            index += 1
            claim_ = Claim()
            claim_.set_source("mimikama")
            url_complete = url
            claim_.set_url(url_complete)
            page = urllib.request.urlopen(url_complete, timeout=5).read()
            soup = BeautifulSoup(page, "lxml")
            soup.prettify()

            # conclusin
            # conclusion=soup.find('div', {"class": "td-post-content"}).find('h2')
            # if conclusion :
            # 	claim_.setConclusion(conclusion.get_text())

            # title
            title = soup.find("h1", {"class": "entry-title"})
            claim_.set_title(title.text)

            # claim
            # claim = soup.find('div', {"class": "td-post-content"}).find('h2')
            # if claim and claim.find_previous('strong'):
            #	claim_.setClaim(claim.find_previous('strong').get_text())
            # else:
            claim_.set_claim(claim_.title)

            # date
            date = soup.find("time", {"class": "entry-date updated td-module-date"})
            # print date

            # print (search_dates(date.get_text())[0][1].strftime("%Y-%m-%d"))
            claim_.set_date(search_dates(date.get_text())[0][1].strftime("%Y-%m-%d"))

            # related links
            divTag = soup.find("div", {"class": "td-post-content"})
            related_links = []
            for link in divTag.findAll('a', href=True):
                related_links.append(link['href'])
            claim_.set_refered_links(related_links)

            body = soup.find("div", {"class": "td-post-content"})
            claim_.set_body(body.get_text())

            claims.append(claim_.generate_dictionary())
        except:
            print("Erro =>" + url)

    # creating a pandas dataframe
    pdf = pd.DataFrame(claims)
    return pdf
