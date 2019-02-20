# -*- coding: utf-8 -*-
import re
from typing import List, Set

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateparser.search import search_dates
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


def get_all_claims(criteria):
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

    # performing a search by each letter, and adding each article to a urls_ var.
    urls_ = {}
    last_page = []
    for page_number in range(1, 500):
        if 0 < criteria.maxClaims <= len(urls_):
            break

        url = "https://africacheck.org/latest-reports/page/" + str(page_number) + "/"
        try:
            page = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(page.text, "lxml")
            soup.prettify()
            links = soup.findAll("div", {"class": "article-content"})
            if (len(links) != 0) or (links != last_page):
                for anchor in links:
                    anchor = anchor.find('a', href=True)
                    ind_ = str(anchor['href'])
                    if ind_ not in list(urls_.keys()):
                        if 0 < criteria.maxClaims <= len(urls_):
                            break
                        if ind_ not in criteria.avoid_url:
                            urls_[ind_] = ind_
                            print("adding " + str(ind_))
                last_page = links
            else:
                print("break!")
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
        # try:
        page = requests.get(url_complete, headers=headers, timeout=5)
        soup = BeautifulSoup(page.text, "lxml")
        soup.prettify("utf-8")

        claim_ = Claim()
        claim_.setUrl(url_complete)
        claim_.setSource("africacheck")

        if (criteria.html):
            claim_.setHtml(soup.prettify("utf-8"))

        # title
        title = soup.find("meta", {"property": "og:title"})
        claim_.setTitle(title['content'])

        # date

        date_ = soup.find('time')
        # print date_["content"]
        if date_:
            date_str = search_dates(date_['datetime'].split(" ")[0])[0][1].strftime("%Y-%m-%d")
            # print date_str
            claim_.setDate(date_str)
        # print claim_.date

        # rating

        truth_rating = ""
        if soup.find("div", {"class": "verdict-stamp"}):
            truth_rating = soup.find("div", {"class": "verdict-stamp"}).get_text()
        if soup.find("div", {"class": "verdict"}):
            truth_rating = soup.find("div", {"class": "verdict"}).get_text()
        if soup.find("div", {"class": "indicator"}):
            truth_rating = soup.find("div", {"class": "indicator"}).get_text()
            if soup.find("div", {"class": "indicator"}).find('span'):
                truth_rating = soup.find("div", {"class": "indicator"}).find('span').get_text()

        claim_.setAlternateName(str(re.sub('[^A-Za-z0-9 -]+', '', truth_rating)).lower().strip())

        # when there is no json

        date_ = soup.find("time", {"class": "datetime"})
        if date_:
            claim_.setDate(date_.get_text())

        # body
        body = soup.find("div", {"id": "main"})
        claim_.setBody(body.get_text())

        # author
        author = soup.find("div", {"class": "sharethefacts-speaker-name"})
        if author:
            claim_.setAuthor(author.get_text())

        # related links
        divTag = soup.find("div", {"id": "main"})
        related_links = []
        for link in divTag.findAll('a', href=True):
            related_links.append(link['href'])
        claim_.set_refered_links(related_links)

        if soup.find("div", {"class": "report-claim"}):
            claim_.setClaim(soup.find("div", {"class": "report-claim"}).find("strong").get_text())
        else:
            claim_.setClaim(claim_.title)

        tags = []

        for tag in soup.findAll('meta', {"property": "article:tag"}):
            tags.append(tag["content"])
        claim_.set_tags(", ".join(tags))

        claims.append(claim_.generate_dictionary())

    # creating a pandas dataframe
    pdf = pd.DataFrame(claims)
    return pdf


class AfricacheckFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def retrieve_listing_page_urls(self) -> List[str]:
        return ["https://africacheck.org/latest-reports/page/1/"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        last_page_link = parsed_listing_page.findAll("a", {"class": "page-numbers"})[-2]['href']
        page_re = re.compile("https://africacheck.org/latest-reports/page/([0-9]+)/")
        max_page = int(page_re.match(last_page_link).group(1))
        return max_page

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> Set[str]:
        urls = self.extract_urls(parsed_listing_page)
        for page_number in tqdm(range(2, number_of_pages)):
            url = "https://africacheck.org/latest-reports/page/" + str(page_number) + "/"
            page = caching.get(url, headers=self.headers, timeout=5)
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls = set.union(urls, self.extract_urls(current_parsed_listing_page))
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = set()
        links = parsed_listing_page.findAll("div", {"class": "article-content"})
        for anchor in links:
            anchor = anchor.find('a', href=True)
            url = str(anchor['href'])
            max_claims = self.configuration.maxClaims
            if 0 < max_claims <= len(urls):
                break
            if url not in self.configuration.avoid_urls:
                urls.add(url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> Claim:
        claim = Claim()
        claim.setUrl(url)
        claim.setSource("africacheck")

        # title
        title = parsed_claim_review_page.find("meta", {"property": "og:title"})
        claim.setTitle(title['content'])

        # date

        date_ = parsed_claim_review_page.find('time')
        # print date_["content"]
        if date_:
            date_str = search_dates(date_['datetime'].split(" ")[0])[0][1].strftime("%Y-%m-%d")
            # print date_str
            claim.setDate(date_str)
        # print claim_.date

        # rating

        truth_rating = ""
        if parsed_claim_review_page.find("div", {"class": "verdict-stamp"}):
            truth_rating = parsed_claim_review_page.find("div", {"class": "verdict-stamp"}).get_text()
        if parsed_claim_review_page.find("div", {"class": "verdict"}):
            truth_rating = parsed_claim_review_page.find("div", {"class": "verdict"}).get_text()
        if parsed_claim_review_page.find("div", {"class": "indicator"}):
            truth_rating = parsed_claim_review_page.find("div", {"class": "indicator"}).get_text()
            if parsed_claim_review_page.find("div", {"class": "indicator"}).find('span'):
                truth_rating = parsed_claim_review_page.find("div", {"class": "indicator"}).find('span').get_text()

        claim.setAlternateName(str(re.sub('[^A-Za-z0-9 -]+', '', truth_rating)).lower().strip())

        # when there is no json

        date_ = parsed_claim_review_page.find("time", {"class": "datetime"})
        if date_:
            claim.setDate(date_.get_text())

        # body
        body = parsed_claim_review_page.find("div", {"id": "main"})
        claim.setBody(body.get_text())

        # author
        author = parsed_claim_review_page.find("div", {"class": "sharethefacts-speaker-name"})
        if author:
            claim.setAuthor(author.get_text())

        # related links
        divTag = parsed_claim_review_page.find("div", {"id": "main"})
        related_links = []
        for link in divTag.findAll('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        if parsed_claim_review_page.find("div", {"class": "report-claim"}):
            claim.setClaim(parsed_claim_review_page.find("div", {"class": "report-claim"}).find("strong").get_text())
        else:
            claim.setClaim(claim.title)

        tags = []

        for tag in parsed_claim_review_page.findAll('meta', {"property": "article:tag"}):
            tags.append(tag["content"])
        claim.set_tags(", ".join(tags))

        return claim
