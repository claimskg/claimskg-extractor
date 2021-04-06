import datetime
import urllib.error
import urllib.parse
import urllib.request

import dateparser
import pandas as pd
from bs4 import BeautifulSoup

from claim_extractor import Claim


def get_all_claims(criteria):
    # performing a search by each letter, and adding each article to a urls_ var.
    now = datetime.datetime.now()
    urls_ = {}
    for year in range(2015, now.year + 1):
        for month in range(1, 13):
            if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
                break
            try:
                page = urllib.request.urlopen(
                    "http://piaui.folha.uol.com.br/lupa/" + str(year) + "/" + str(month) + "/").read()
            except:
                break
            soup = BeautifulSoup(page, "lxml")
            soup.prettify()
            links = soup.find('div', {"class": "lista-noticias"}).findAll('a', href=True)
            if len(links) != 0:
                for anchor in links:
                    if (anchor['href'] not in list(urls_.keys())):
                        urls_[anchor['href']] = [year, month]
                        print("adding " + str(anchor['href']))
                        if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
                            break
            else:
                print ("break!")
                break

    claims = []
    index = 0
    # visiting each article's dictionary and extract the content.
    for url in list(urls_.keys()):
        print(str(index) + "/" + str(len(list(urls_.keys()))) + " extracting " + str(url))
        index += 1
        try:
            claim_ = Claim()
            claim_.set_source("lupa")
            url_complete = url
            claim_.set_url(url_complete)
            page = urllib.request.urlopen(url_complete).read()
            soup = BeautifulSoup(page, "lxml")
            soup.prettify()

            if (criteria.html):
                claim_.setHtml(soup.prettify())

            # conclusin
            conclusion = soup.find('div', {"class": "etiqueta"})
            if conclusion:
                claim_.setConclusion(conclusion.get_text())

            # title
            title = soup.find("h2", {"class": "bloco-title"})
            claim_.set_title(title.text)

            # claim
            claim = soup.find('div', {"class": "post-inner"}).find('div', {"class": "etiqueta"})
            if claim and claim.find_previous('strong'):
                claim_.set_claim(claim.find_previous('strong').get_text())
            else:
                claim_.set_claim(claim_.title)

            # date
            date = soup.find("div", {"class": "bloco-meta"})
            claim_.set_date(
                dateparser.parse(date.text.split("|")[0], settings={'DATE_ORDER': 'DMY'}).strftime("%Y-%m-%d"))

            # related links
            divTag = soup.find("div", {"class": "post-inner"})
            related_links = []
            for link in divTag.findAll('a', href=True):
                related_links.append(link['href'])
            claim_.set_refered_links(related_links)

            # related links
            body = soup.find("div", {"class": "post-inner"})
            claim_.set_body(body.get_text())

            # tags
            tags_ = [t.text for t in soup.findAll('a', {'rel': 'tag'})]
            claim_.set_tags(tags_)

            claims.append(claim_.generate_dictionary())
        except:
            print("error=>" + str(url_complete))

    # creating a pandas dataframe
    pdf = pd.DataFrame(claims)
    return pdf
