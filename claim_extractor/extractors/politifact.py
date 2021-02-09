# -*- coding: utf-8 -*-
import re
from typing import List, Set

from bs4 import BeautifulSoup
from dateparser.search import search_dates
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


class PolitifactFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def retrieve_listing_page_urls(self) -> List[str]:
        return ["https://www.politifact.com/factchecks/list/"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        return -1

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = self.extract_urls(parsed_listing_page)
        page_number = 2
        while True:
            url = listing_page_url + "?page=" + str(page_number)
            page = caching.get(url, headers=self.headers, timeout=5)
            if page is not None:
                current_parsed_listing_page = BeautifulSoup(page, "lxml")
            else:
                break

            nav_buttons = current_parsed_listing_page.find_all("section", attrs={'class': 't-row'})
            nav_buttons = nav_buttons[-1].find_all("li", attrs={'class': 'm-list__item'})

            if len(nav_buttons) == 1:
                break
            else:
                urls += self.extract_urls(current_parsed_listing_page)
            page_number += 1
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = list()
        links = parsed_listing_page.findAll("div", {"class": "m-statement__content"})
        for anchor in links:
            anchor = anchor.find('a', href=True)
            url = "http://www.politifact.com" + str(anchor['href'])
            max_claims = self.configuration.maxClaims
            if 0 < max_claims <= len(urls):
                break
            if url not in self.configuration.avoid_urls:
                urls.append(url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claim = Claim()
        claim.set_url(url)
        claim.set_source("politifact")

        # title
        title = parsed_claim_review_page.find("div", {"class": "m-statement__quote"})
        claim.set_claim(title.text)

        # Claim
        summary = parsed_claim_review_page.find("meta", attrs={'name': 'description'})
        claim.set_title(summary.text)

        # date
        date_claimed = parsed_claim_review_page.find('div', {"class": "m-statement__desc"}).find("p")
        if date_claimed:
            date_str = search_dates(date_claimed.text)[0][1].strftime("%Y-%m-%d")
            claim.set_date(date_str)

        # rating
        meter = parsed_claim_review_page.find("div", attrs={'class': 'm-statement__meter'})
        rating_image = meter.find('img', attrs={'class': 'c-image__original'})
        rating = rating_image['alt']
        claim.set_rating(rating)

        # # rating
        # rating_div = parsed_claim_review_page.find("div", {"itemprop": "reviewRating"})
        # if rating_div:
        #     rating_value = rating_div.find("div", {"itemprop": "ratingValue"})
        #     if rating_value:
        #         claim.rating_value = rating_value.text
        #     worst_rating = rating_div.find("div", {"itemprop": "worstRating"})
        #     if worst_rating:
        #         claim.worst_rating = worst_rating.text
        #
        #     best_rating = rating_div.find("div", {"itemprop": "bestRating"})
        #     if best_rating:
        #         claim.best_rating = best_rating.text
        #
        #     alternate_name = rating_div.find("div", {"itemprop": "alternateName"})
        #     if alternate_name:
        #         claim.alternate_name = alternate_name.text
        # else:
        #     statement_detail = parsed_claim_review_page.find("img", {"class", "statement-detail"})
        #     if statement_detail:
        #         claim.alternate_name = statement_detail['alt']

        # body
        body = parsed_claim_review_page.find("article", {"class": "m-textblock"})
        claim.set_body(body.get_text())

        # author
        author_content = parsed_claim_review_page.find("p", {"class": "m-author__content"})
        if author_content:
            author = author_content.find("a").text
            claim.set_author(author)
            date_str = search_dates(author_content.find('span').text)[0][1].strftime("%Y-%m-%d")
            claim.set_date_published(date_str)

        # # date published
        # if author_content:
        #     meta_text = author_content.text
        #     if "on" in meta_text:
        #         meta_text = meta_text.split(" on ")[1]
        #     if "in" in meta_text:
        #         meta_text = meta_text.split(" in ")[0]
        #     if meta_text:
        #         date_claimed = search_dates(meta_text)
        #         if date_claimed:
        #             date_claimed = date_claimed[0][1].strftime("%Y-%m-%d")
        #             claim.set_date_published(date_claimed)
        # else:
        #     rating_div = parsed_claim_review_page.find("div", {"itemprop": "itemReviewed"})
        #     if rating_div and rating_div.find("div", {"itemprop": "datePublished"}):
        #         claim.set_date_published(rating_div.find("div", {"itemprop": "datePublished"}).get_text())

        # related links
        related_links = []
        for link in body.find_all('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        tags = []
        statement_body = parsed_claim_review_page.find("div", {"class", "m-statement__body"})

        if statement_body:
            topics = statement_body.find("ul", {"class", "m-list"}).find_all("a")
            for link in topics:
                text = link['title']
                tags.append(text)
            claim.set_tags(",".join(tags))

        return [claim]
