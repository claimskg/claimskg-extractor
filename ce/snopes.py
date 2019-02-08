# -*- coding: utf-8 -*-
import datetime
import re
import urllib2

import dateparser
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

import Claim as claim_obj


def get_all_claims(criteria):
    print criteria.maxClaims
    now = datetime.datetime.now()

    # Finding number of pages
    # https://www.snopes.com/fact-check/page/2/
    page_2 = urllib2.urlopen("https://www.snopes.com/fact-check/page/2/").read()
    title_text = BeautifulSoup(page_2, "lxml").find(
        "title").text  # Format u'Fact Checks Archive | Page 2 of 1069 | Snopes.com'
    max_page_pattern = re.compile("Page [0-9]+ of ([0-9+]+)")
    result = max_page_pattern.match(title_text.split("|")[1].strip())
    max_page = result.group(1)

    # performing a search by each letter, and adding each article to a urls_ var.
    urls_ = {}
    for page_number in tqdm(range(1, int(max_page))):
        if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
            break
        try:
            page = urllib2.urlopen("https://www.snopes.com/fact-check/page/" + str(page_number) + "/").read()
        except:
            break
        soup = BeautifulSoup(page, "lxml")
        soup.prettify()
        links = soup.findAll('a', {"class": "link"}, href=True)
        if len(links) != 0:
            for anchor in links:
                ind_ = anchor['href']
                if (ind_ not in urls_.keys()):
                    if (criteria.maxClaims > 0 and len(urls_) >= criteria.maxClaims):
                        break
                    if (ind_ not in criteria.avoid_url):
                        urls_[ind_] = page_number
                        # print "adding " + str(ind_)
        else:
            # print ("break!")
            break

    claims = []
    index = 0
    # visiting each article's dictionary and extract the content.
    for url in tqdm(urls_.keys()):
        # print str(index) + "/" + str(len(urls_.keys())) + " extracting " + str(url)
        index += 1

        url_complete = str(url)

        # print url_complete
        try:
            page = urllib2.urlopen(url_complete).read().decode('utf-8', 'ignore')
            soup = BeautifulSoup(page, "lxml")
            soup.prettify("utf-8")

            claim_ = claim_obj.Claim()
            claim_.setUrl(url_complete)
            claim_.setSource("snopes")

            if (criteria.html):
                claim_.setHtml(soup.prettify("utf-8"))

            # title
            # if (soup.find("h1",{"class":"content-head__title"}) and len(soup.find("h1",{"class":"content-head__title"}).get_text().split("?"))>1):
            title = soup.find("h1", {"class": "card-title"})
            claim_.setTitle(title.text)

            # date

            date_ = soup.find('span', {"class": "date-published"})
            # print date_["content"]
            if date_:
                date_str = dateparser.parse(date_.text).strftime("%Y-%m-%d")
                # print date_str
                claim_.setDate(date_str)
                claim_.setDatePublished(date_str)
            # print claim_.date

            # body
            body = soup.find("div", {"class": "post-body-card"})
            card = body.find("div", {"class": "card-body"})
            ads = card.findAll("div", {"class": "creative"})
            for ad in ads:
                ad.decompose()

            ads = card.findAll("div", {"class": "snopes-bt"})
            for ad in ads:
                ad.decompose()

            text = ""
            contents = card.findChildren()
            for child in contents:
                text += child.text

            claim_.setBody(body.get_text())

            # author
            author = soup.find("a", {"class": "author"})
            if (author):
                claim_.setAuthor(author.text)

            # sameas
            # obj = soup.find("span", {"itemprop": "itemReviewed"})
            # if (obj and obj.find("meta", {"itemprop": "sameAs"})):
            #     claim_.setSameAs(obj.find("meta", {"itemprop": "sameAs"})['content'])

            # samdatepublished
            # obj = soup.find("span", {"itemprop": "itemReviewed"})
            # if (obj and obj.find("meta", {"itemprop": "datePublished"})):
            #     date_ = obj.find("meta", {"itemprop": "datePublished"})['content']
            #     if (date_.split("T") > 1):
            #         claim_.setDatePublished(date_.split("T")[0])

            # rating
            # obj = soup.find("span", {"itemprop": "reviewRating"})
            # if (obj):
            #     claim_.ratingValue = ""
            #     claim_.worstRating = ""
            #     claim_.bestRating = ""
            claim_.alternateName = soup.find("span", {"class": "rating-name"}).text

            # related links
            divTag = soup.find("div", {"class": "post-body-card"})
            related_links = []
            for link in divTag.findAll('a', href=True):
                related_links.append(link['href'])
            claim_.setRefered_links(related_links)

            claim_.setClaim(soup.find('p', {"class": "claim"}).text)

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
