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
    for type_ in ["verdadeiro", "impreciso", "exagerado", "contraditorio", "insustentavel", "falso"]:
        for page_number in range(1, 500):
            if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
                break
            try:
                page = urllib.request.urlopen(
                    "http://aosfatos.org/noticias/checamos/" + str(type_) + "/?page=" + str(page_number)).read()
            except:
                break
            soup = BeautifulSoup(page, "lxml")
            soup.prettify()
            links = soup.findAll('a', {"class": "card third"}, href=True)
            if len(links) != 0:
                for anchor in links:
                    if (anchor['href'] not in list(urls_.keys())):
                        if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
                            break
                        urls_[anchor['href']] = type_
                        print("adding " + str(anchor['href']))
            else:
                print ("break!")
                break

    claims = []
    index = 0
    # visiting each article's dictionary and extract the content.
    for url, conclusion in urls_.items():
        print(str(index) + "/" + str(len(list(urls_.keys()))) + " extracting " + str(url))
        index += 1

        url_complete = "https://aosfatos.org/" + str(url)

        # print url_complete
        page = urllib.request.urlopen(url_complete).read().decode('utf-8', 'ignore')
        soup = BeautifulSoup(page, "lxml")
        soup.prettify("utf-8")

        for claim_element in soup.findAll("blockquote"):
            claim_ = Claim()
            claim_.set_url(url_complete)
            claim_.set_source("aosfatos")

            # date
            date_ = soup.find('p', {"class": "publish_date"})
            if date_:
                date_str = date_.get_text().replace("\n", "").replace("  ", "").split(",")[0]
                claim_.set_date(dateparser.parse(date_str).strftime("%Y-%m-%d"))

            # title
            title = soup.findAll("h1")
            claim_.set_title(title[1].text)

            # body
            body = soup.find("article")
            claim_.set_body(body.get_text().replace("\n", "").replace("TwitterFacebookE-mailWhatsApp", ""))

            # related links
            divTag = soup.find("article").find("hr")
            related_links = []
            for link in divTag.find_all_next('a', href=True):
                related_links.append(link['href'])
            claim_.set_refered_links(related_links)

            # claim
            claim_.set_claim(claim_element.get_text())
            # if (claim_element.find_previous_sibling("figure") and claim_element.find_previous_sibling("figure").findAll(
            #         "figcaption")):
            # claim_.setConclusion(
            #     claim_element.find_previous_sibling("figure").findAll("figcaption")[-1:][0].get_text())
            # print claim_.claim.decode("utf-8") + " ====> "
            # print claim_.conclusion.decode("utf-8")
            # print "-->"+ str(claim_.conclusion)

            claims.append(claim_.generate_dictionary())

    # creating a pandas dataframe
    pdf = pd.DataFrame(claims)
    return pdf
