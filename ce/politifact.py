# -*- coding: utf-8 -*-
import datetime
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateparser.search import search_dates
from tqdm import tqdm

import Claim as claim_obj


def get_all_claims(criteria):
    headers = {
        'user-agent': 'Mozilla/5.5 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

    # print criteria.maxClaims
    # performing a search by each letter, and adding each article to a urls_ var.
    now = datetime.datetime.now()
    urls_ = {}
    types = ["true", "mostly-true", "half-true", "barely-true", "false", "pants-fire", "no-flip", "half-flip",
             "full-flop"]
    last_page = []
    for type_ in types:
        print ("Fetching " + str(type_) + " claims pages...")
        type_first_page_url = "https://www.politifact.com/truth-o-meter/rulings/false/"
        page = requests.get(type_first_page_url, headers=headers, timeout=5)
        soup = BeautifulSoup(page.text, "lxml")
        page_text = soup.find("span", {"class": "step-links__current"}).text.strip()
        page_re = re.compile("Page [0-9]+ of ([0-9]+)")
        max_page = int(page_re.match(page_text).group(1))

        for page_number in tqdm(range(1, max_page)):
            if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
                break
            url = "http://www.politifact.com/truth-o-meter/rulings/" + str(type_) + "/?page=" + str(page_number)
            try:
                page = requests.get(url, headers=headers, timeout=5)
                soup = BeautifulSoup(page.text, "lxml")
                # soup.prettify()

                links = soup.findAll("p", {"class": "statement__text"})
                if (len(links) != 0) or (links != last_page):
                    for anchor in links:
                        anchor = anchor.find('a', {"class": "link"}, href=True)
                        ind_ = "http://www.politifact.com" + str(anchor['href'])
                        if (ind_ not in urls_.keys()):
                            if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
                                break
                            if (ind_ not in criteria.avoid_url):
                                urls_[ind_] = type_
                                # print "adding " + str(ind_)
                    last_page = links
                else:
                    # print ("break!")
                    break
            except:
                print "error=>" + str(url)

    claims = []
    index = 0
    # visiting each article's dictionary and extract the content.
    for url in tqdm(urls_.keys()):
        # print str(index) + "/" + str(len(urls_.keys())) + " extracting " + str(url)
        index += 1

        url_complete = str(url)

        # print url_complete
        try:
            page = requests.get(url_complete, headers=headers, timeout=5)
            soup = BeautifulSoup(page.text, "lxml")
            soup.prettify("utf-8")

            claim_ = claim_obj.Claim()
            claim_.setUrl(url_complete)
            claim_.setSource("politifact")

            if (criteria.html):
                claim_.setHtml(soup.prettify("utf-8"))

            # title
            # if (soup.find("h1",{"class":"content-head__title"}) and len(soup.find("h1",{"class":"content-head__title"}).get_text().split("?"))>1):
            title = soup.find("h1", {"class": "article__title"})
            claim_.setTitle(title.text)

            # date

            date_ = soup.find('div', {"class": "widget__content"}).find("p")
            # print date_["content"]
            if date_:
                date_str = search_dates(date_.text)[0][1].strftime("%Y-%m-%d")
                # print date_str
                claim_.setDate(date_str)
            # print claim_.date

            # rating
            obj = soup.find("div", {"itemprop": "reviewRating"})
            if (obj):
                claim_.ratingValue = obj.find("div", {"itemprop": "ratingValue"}).text
                claim_.worstRating = obj.find("div", {"itemprop": "worstRating"}).text
                claim_.bestRating = obj.find("div", {"itemprop": "bestRating"}).text
                claim_.alternateName = obj.find("div", {"itemprop": "alternateName"}).text
            # else:
                # claim_.setConclusion(conclusion)

            # body
            body = soup.find("div", {"class": "article__text"})
            claim_.setBody(body.get_text())

            # author
            author = soup.find("div", {"itemprop": "itemReviewed"})
            if (author and author.find("div", {"itemprop": "author"})):
                claim_.setAuthor(
                    author.find("div", {"itemprop": "author"}).find("div", {"itemprop": "name"}).get_text())

            # sameas
            obj = soup.find("div", {"itemprop": "itemReviewed"})
            if (obj and obj.find("div", {"itemprop": "sameAs"})):
                claim_.setSameAs(obj.find("div", {"itemprop": "sameAs"}).get_text())

            # sameAs
            obj = soup.find("div", {"itemprop": "itemReviewed"})
            if (obj and obj.find("div", {"itemprop": "datePublished"})):
                claim_.setDatePublished(obj.find("div", {"itemprop": "datePublished"}).get_text())

            # related links
            divTag = soup.find("div", {"class": "article__text"})
            related_links = []
            for link in divTag.findAll('a', href=True):
                related_links.append(link['href'])
            claim_.setRefered_links(related_links)

            claim_.setClaim(soup.find("h1", {"class": "article__title"}).text)

            tags = []

            for tag in soup.findAll('meta', {"property": "article:tag"}):
                # print "achou"
                tags.append(tag["content"])
            claim_.setTags(", ".join(tags))

            claims.append(claim_.generate_dictionary())
        except:
            print "Error ->" + str(url_complete)

    # creating a pandas dataframe
    pdf = pd.DataFrame(claims)
    return pdf
