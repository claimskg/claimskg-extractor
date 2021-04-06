# -*- coding: utf-8 -*-
import re
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateparser.search import search_dates
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import find_by_text, FactCheckingSiteExtractor, caching


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
            claim_.set_url(url_complete)
            claim_.set_source("washingtonpost")

            if criteria.html:
                claim_.setHtml(soup.prettify("utf-8"))

            # title
            title = soup.find("h1", {"class": "article__title"})
            claim_.set_title(title.text)

            # date

            date_ = soup.find('div', {"class": "widget__content"}).find("p")
            if date_:
                date_str = search_dates(date_.text)[0][1].strftime("%Y-%m-%d")
                claim_.set_date(date_str)

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


class WashingtonpostFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)
        self.date_regexp = re.compile("^([0-9]{4})/([0-9]{2})/([0-9]{2})*")

    def retrieve_listing_page_urls(self) -> List[str]:
        return ["https://www.washingtonpost.com/news/fact-checker/?utm_term=.c0f1538d1850"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        count = 26
        url = "https://checkyourfact.com/page/" + str(count + 1)
        result = caching.get(url, headers=self.headers, timeout=10)
        if result:
            while result:
                count += 1
                url = "https://www.washingtonpost.com/news/fact-checker/page/" + str(count)
                result = caching.get(url, headers=self.headers, timeout=10)
        else:
            count -= 1

        return count

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = self.extract_urls(parsed_listing_page)

        for page_number in tqdm(range(2, number_of_pages)):
            url = "https://www.washingtonpost.com/news/fact-checker/page/" + str(page_number) + "/"
            page = caching.get(url, headers=self.headers, timeout=5)
            if page:
                current_parsed_listing_page = BeautifulSoup(page, "lxml")
                urls +=self.extract_urls(current_parsed_listing_page)
            else:
                break

        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = list()
        links = parsed_listing_page.find('articles').findAll('a', href=True)
        for anchor in links:
            url = "https://checkyourfact.com" + str(anchor['href'])
            max_claims = self.configuration.maxClaims
            if 0 < max_claims <= len(urls):
                break
            if url not in self.configuration.avoid_urls:
                urls.append(url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claim = Claim()
        claim.set_url(url)
        claim.set_source("checkyourfact")

        # title
        title = parsed_claim_review_page.find('article').find("h1")
        claim.set_title(title.text.replace("FACT CHECK: ", ""))

        url_date = url.replace("https://checkyourfact.com/", "").replace("/", " ").split(" ")
        claim.set_date(url_date[0] + "-" + url_date[1] + "-" + url_date[2])

        # body
        body = parsed_claim_review_page.find("article")
        claim.set_body(body.get_text())

        # related links
        div_tag = parsed_claim_review_page.find("article")
        related_links = []
        for link in div_tag.findAll('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        claim.set_claim(claim.title)

        # rating
        rating = find_by_text(parsed_claim_review_page, "Verdict", "span")
        if rating:
            rating_text = rating[0].text.split(":")[-1].strip()
            claim.set_rating(rating_text)
        else:
            pass

        tags = []

        for tag in parsed_claim_review_page.findAll('meta', {"property": "article:tag"}):
            tags.append(tag["content"])
        claim.set_tags(", ".join(tags))
        if len(claim.rating) == 0:
            return []
        else:
            return [claim]
