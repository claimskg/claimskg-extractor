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
    types = ["true", "mostly-true", "half-true", "barely-true", "false", "pants-fire", "no-flip", "half-flip",
             "full-flop"]
    last_page = []
    for page_number in range(1, 500):
        if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
            break
        url = "https://www.channel4.com/news/factcheck/page/" + str(page_number)
        # url="http://www.politifact.com/truth-o-meter/rulings/"+str(type_)+"/?page="+str(page_number)
        try:
            page = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(page.text, "lxml")
            soup.prettify()

            links = soup.findAll("li", {"class": "feature factcheck"})
            if (len(links) != 0) or (links != last_page):
                for anchor in links:
                    anchor = anchor.find('a', {"class": "permalink"}, href=True)
                    ind_ = str(anchor['href'])
                    if (ind_ not in list(urls_.keys())):
                        if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
                            break
                        if (ind_ not in criteria.avoid_url):
                            urls_[ind_] = ind_
                            print("adding " + str(ind_))
                last_page = links
            else:
                print ("break!")
                break
        except:
            print("error=>" + str(url))

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
            claim_.set_source("channel4")

            if (criteria.html):
                claim_.setHtml(soup.prettify("utf-8"))

            # title
            # if (soup.find("h1",{"class":"content-head__title"}) and len(soup.find("h1",{"class":"content-head__title"}).get_text().split("?"))>1):
            title = soup.find("div", {"class": "factcheck-article-header"}).find("h1").get_text()
            claim_.set_title(title)

            # date

            date_ = soup.find('li', {"class": "pubDateTime"})
            # print date_["content"]
            if date_:
                date_str = search_dates(date_['data-time'])[0][1].strftime("%Y-%m-%d")
                # print date_str
                claim_.set_date(date_str)
            # print claim_.date

            # body
            body = soup.find("div", {"class": "article-body article-main"})
            claim_.set_body(body.get_text())

            # related links
            divTag = soup.find("div", {"class": "article-body article-main"})
            related_links = []
            for link in divTag.findAll('a', href=True):
                related_links.append(link['href'])
            claim_.set_refered_links(related_links)

            claim_.set_claim(title)

            tags = []

            for tag in soup.findAll('meta', {"property": "article:tag"}):
                # print "achou"
                tags.append(tag["content"])
            claim_.set_tags(", ".join(tags))

            # if (claim_.conclusion.replace(" ","")=="" or claim_.claim.replace(" ","")==""):
            # 	print claim_.conclusion
            # 	print claim_.claim
            # 	raise ValueError('No conclusion or claim')

            claims.append(claim_.generate_dictionary())
        except:
            print("Error ->" + str(url_complete))

    # creating a pandas dataframe
    pdf = pd.DataFrame(claims)
    return pdf
