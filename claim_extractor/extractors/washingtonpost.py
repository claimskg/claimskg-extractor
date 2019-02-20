# -*- coding: utf-8 -*-

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateparser.search import search_dates

from claim_extractor import Claim


def get_all_claims(criteria):
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

    # performing a search by each letter, and adding each article to a urls_ var.
    urls_ = {}
    for page_number in range(1, 500):
        if 0 < criteria.maxClaims <= len(urls_):
            break
        url = "https://www.washingtonpost.com/news/fact-checker/page/" + str(page_number) + "/"
        if page_number == 1:
            url = "https://www.washingtonpost.com/news/fact-checker/?utm_term=.c0f1538d1850"

        # try:
        print(url)
        page = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(page.text, "lxml")
        soup.prettify()
        print(page.text)
        links = soup.findAll("div", {"class": "story-headline"})
        print(links)
        if len(links) == 0:
            break

        for anchor in links:
            anchor = anchor.find("a")
            ind_ = str(anchor['href'])
            if ind_ not in list(urls_.keys()):
                if 0 < criteria.maxClaims <= len(urls_):
                    break
                urls_[ind_] = ind_

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
            claim_.setUrl(url_complete)
            claim_.setSource("washingtonpost")

            if criteria.html:
                claim_.setHtml(soup.prettify("utf-8"))

            # title
            title = soup.find("h1", {"class": "article__title"})
            claim_.setTitle(title.text)

            # date

            date_ = soup.find('div', {"class": "widget__content"}).find("p")
            if date_:
                date_str = search_dates(date_.text)[0][1].strftime("%Y-%m-%d")
                claim_.setDate(date_str)

            # body
            body = soup.find("div", {"class": "article__text"})
            claim_.setBody(body.get_text())

            # related links
            divTag = soup.find("div", {"class": "article__text"})
            related_links = []
            for link in divTag.findAll('a', href=True):
                related_links.append(link['href'])
            claim_.set_refered_links(related_links)

            claim_.setClaim(soup.find("h1", {"class": "article__title"}).text)
            tags = []

            for tag in soup.findAll('meta', {"property": "article:tag"}):
                tags.append(tag["content"])
            claim_.set_tags(", ".join(tags))

            claims.append(claim_.generate_dictionary())
        except:
            print("Error ->" + str(url_complete))

    # creating a pandas dataframe
    pdf = pd.DataFrame(claims)
    return pdf
