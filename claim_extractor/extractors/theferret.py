# -*- coding: utf-8 -*-
import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateparser.search import search_dates

from claim_extractor import Claim


def get_all_claims(criteria):
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

    # print criteria.maxClaims
    # performing a search by each letter, and adding each article to a urls_ var.
    now = datetime.datetime.now()
    urls_ = {}
    last_page = []
    for page_number in range(1, 500):
        if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
            break
        url = "https://theferret.scot/category/fact-check/page/" + str(page_number) + "/"
        # try:
        page = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(page.text, "lxml")
        soup.prettify()

        links = soup.findAll("h1", {"class": "entry-title"})
        if (len(links) != 0) or (links != last_page):
            for anchor in links:
                anchor = anchor.find('a', {"rel": "bookmark"}, href=True)
                ind_ = str(anchor['href'])
                if (ind_ not in list(urls_.keys())):
                    if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
                        break
                    urls_[ind_] = page
                    print("adding " + str(ind_))
            last_page = links
        else:
            print("break!")
            break
    # except:
    #	print "error=>"+str(url)

    claims = []
    index = 0
    # visiting each article's dictionary and extract the content.
    for url, conclusion in urls_.items():
        print(str(index) + "/" + str(len(list(urls_.keys()))) + " extracting " + str(url))
        index += 1

        url_complete = str(url)

        # print url_complete
        try:
            page = requests.get(url_complete, headers=headers, timeout=5)
            soup = BeautifulSoup(page.text, "lxml")
            soup.prettify("utf-8")

            claim_ = Claim()
            claim_.set_url(url_complete)
            claim_.set_source("theferret")

            if (criteria.html):
                claim_.setHtml(soup.prettify("utf-8"))

            # title
            # if (soup.find("h1",{"class":"content-head__title"}) and len(soup.find("h1",{"class":"content-head__title"}).get_text().split("?"))>1):
            title = soup.find("h1", {"class": "cover-title"})
            claim_.set_title(title.text)

            # date

            date_ = soup.find('div', {"class": "widget__content"}).find("p")
            # print date_["content"]
            if date_:
                date_str = search_dates(date_.text)[0][1].strftime("%Y-%m-%d")
                # print date_str
                claim_.set_date(date_str)
            # print claim_.date

            # body
            body = soup.find("div", {"class": "article__text"})
            claim_.set_body(body.get_text())

            # related links
            divTag = soup.find("div", {"class": "article__text"})
            related_links = []
            for link in divTag.findAll('a', href=True):
                related_links.append(link['href'])
            claim_.set_refered_links(related_links)

            claim_.set_claim(soup.find("h1", {"class": "article__title"}).text)
            claim_.setConclusion(conclusion)

            tags = []

            for tag in soup.findAll('meta', {"property": "article:tag"}):
                # print "achou"
                tags.append(tag["content"])
            claim_.set_tags(", ".join(tags))

            claims.append(claim_.generate_dictionary())
        except:
            print("Error ->" + str(url_complete))

    # creating a pandas dataframe
    pdf = pd.DataFrame(claims)
    return pdf
