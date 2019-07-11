# -*- coding: utf-8 -*-
import datetime
import urllib.error
import urllib.parse
import urllib.request

import dateparser
import pandas as pd
from bs4 import BeautifulSoup

from claim_extractor import Claim


def get_all_claims(criteria):
    print(criteria.maxClaims)
    # performing a search by each letter, and adding each article to a urls_ var.
    now = datetime.datetime.now()
    urls_ = {}
    for page_number in range(1, 500):
        if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
            break
        try:
            page = urllib.request.urlopen(
                "https://g1.globo.com/e-ou-nao-e/index/feed/pagina-" + str(page_number) + ".ghtml").read()
        except:
            break
        soup = BeautifulSoup(page, "lxml")
        soup.prettify()
        links = soup.findAll('a', {"class": "feed-post-link"}, href=True)
        if len(links) != 0:
            for anchor in links:
                if (anchor['href'] not in list(urls_.keys())):
                    if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
                        break
                    urls_[anchor['href']] = page_number
                    print("adding " + str(anchor['href']))
        else:
            print("break!")
            break

    claims = []
    index = 0
    # visiting each article's dictionary and extract the content.
    for url, conclusion in urls_.items():
        print(str(index) + "/" + str(len(list(urls_.keys()))) + " extracting " + str(url))
        index += 1

        url_complete = str(url)

        # print url_complete
        page = urllib.request.urlopen(url_complete).read().decode('utf-8', 'ignore')
        soup = BeautifulSoup(page, "lxml")
        soup.prettify("utf-8")

        claim_ = Claim()
        claim_.set_url(url_complete)
        claim_.set_source("g1")

        if (criteria.html):
            claim_.setHtml(soup.prettify("utf-8"))

        try:
            # title
            # if (soup.find("h1",{"class":"content-head__title"}) and len(soup.find("h1",{"class":"content-head__title"}).get_text().split("?"))>1):
            title = soup.find("h1", {"class": "content-head__title"})
            claim_.set_title(title.text)

            # date

            date_ = soup.find('time', {"itemprop": "datePublished"})
            if date_:
                date_str = date_.get_text().split(" ")[1]
                claim_.set_date(dateparser.parse(date_str, settings={'DATE_ORDER': 'DMY'}).strftime("%Y-%m-%d"))
            # print claim_.date

            # body
            body = soup.find("article")
            claim_.set_body(body.get_text().replace("\n", "").replace("TwitterFacebookE-mailWhatsApp", ""))

            # related links
            divTag = soup.find("article", {"itemprop": "articleBody"})
            related_links = []
            for link in divTag.findAll('a', href=True):
                related_links.append(link['href'])
            claim_.set_refered_links(related_links)

            # claim
            claim_conclusion = soup.find("h1", {"class": "content-head__title"}).get_text()
            # claim_.setClaim(claim_conclusion)
            # if (len(claim_conclusion.split("?"))>1):
            claim_.set_claim(claim_conclusion.split("?")[0])
            claim_.setConclusion(claim_conclusion.split("?")[1])
            # if (claim_element.find_previous_sibling("figure") and claim_element.find_previous_sibling("figure").findAll("figcaption")):
            # 	claim_.setConclusion(claim_element.find_previous_sibling("figure").findAll("figcaption")[-1:][0].get_text())
            # print claim_.claim.decode("utf-8") + " ====> "
            # print claim_.conclusion.decode("utf-8")
            # print "-->"+ str(claim_.conclusion)

            claims.append(claim_.generate_dictionary())
        except:
            print("Error ->" + str(url_complete))

    # creating a pandas dataframe
    pdf = pd.DataFrame(claims)
    return pdf
