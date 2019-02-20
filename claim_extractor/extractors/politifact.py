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
        listings_url = "https://www.politifact.com/truth-o-meter/rulings/"
        page = caching.get(listings_url, headers=self.headers, timeout=5)
        parsed = BeautifulSoup(page, "lxml")
        main_tag = parsed.find("main", {"class": "main"})  # type: BeautifulSoup
        links = main_tag.find_all("a", href=True)
        return ["http://www.politifact.com" + link['href'] for link in links]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        page_text = parsed_listing_page.find("span", {"class": "step-links__current"}).text.strip()
        page_re = re.compile("Page [0-9]+ of ([0-9]+)")
        max_page = int(page_re.match(page_text).group(1))
        return max_page

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> Set[str]:
        urls = self.extract_urls(parsed_listing_page)
        for page_number in tqdm(range(2, number_of_pages)):
            url = listing_page_url + "?page=" + str(page_number)
            page = caching.get(url, headers=self.headers, timeout=5)
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls = set.union(urls, self.extract_urls(current_parsed_listing_page))
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = set()
        links = parsed_listing_page.findAll("p", {"class": "statement__text"})
        for anchor in links:
            anchor = anchor.find('a', {"class": "link"}, href=True)
            url = "http://www.politifact.com" + str(anchor['href'])
            max_claims = self.configuration.maxClaims
            if 0 < max_claims <= len(urls):
                break
            if url not in self.configuration.avoid_urls:
                urls.add(url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> Claim:
        claim = Claim()
        claim.setUrl(url)
        claim.setSource("politifact")

        # title
        title = parsed_claim_review_page.find("h1", {"class": "article__title"})
        claim.setTitle(title.text)

        # date
        date = parsed_claim_review_page.find('div', {"class": "widget__content"}).find("p")
        if date:
            date_str = search_dates(date.text)[0][1].strftime("%Y-%m-%d")
            claim.setDate(date_str)

        # rating
        rating_div = parsed_claim_review_page.find("div", {"itemprop": "reviewRating"})
        if rating_div:
            rating_value = rating_div.find("div", {"itemprop": "ratingValue"})
            if rating_value:
                claim.rating_value = rating_value.text
            worst_rating = rating_div.find("div", {"itemprop": "worstRating"})
            if worst_rating:
                claim.worst_rating = worst_rating.text

            best_rating = rating_div.find("div", {"itemprop": "bestRating"})
            if best_rating:
                claim.best_rating = best_rating.text

            alternate_name = rating_div.find("div", {"itemprop": "alternateName"})
            if alternate_name:
                claim.alternate_name = alternate_name.text
        else:
            statement_detail = parsed_claim_review_page.find("img", {"class", "statement-detail"})
            if statement_detail:
                claim.alternate_name = statement_detail['alt']

        # body
        body = parsed_claim_review_page.find("div", {"class": "article__text"})
        claim.setBody(body.get_text())

        # author
        author = parsed_claim_review_page.find("div", {"itemprop": "itemReviewed"})
        if author:
            author = author.find("div", {"itemprop": "author"})
            author_text = author.text
            claim.setAuthor(author_text)

        # same as
        rating_div = parsed_claim_review_page.find("div", {"itemprop": "itemReviewed"})
        if rating_div and rating_div.find("div", {"itemprop": "sameAs"}):
            claim.setSameAs(rating_div.find("div", {"itemprop": "sameAs"}).get_text())

        # sameAs
        rating_div = parsed_claim_review_page.find("div", {"itemprop": "itemReviewed"})
        if rating_div and rating_div.find("div", {"itemprop": "datePublished"}):
            claim.setDatePublished(rating_div.find("div", {"itemprop": "datePublished"}).get_text())

        # related links
        div_tag = parsed_claim_review_page.find("div", {"class": "article__text"})
        related_links = []
        for link in div_tag.findAll('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        claim.setClaim(parsed_claim_review_page.find("div", {"class": "statement__text"}).text.strip())

        tags = []
        about_widget = parsed_claim_review_page.find("div", {"class", "widget_about-article"})
        about_widget_contents = about_widget.find("div", {"class", "widget__content"})
        for p in about_widget_contents.findAll("p"):
            text = p.text
            if "Subjects:" in text:
                for subject in p.findAll("a"):
                    tags.append(subject.text)

        claim.set_tags(",".join(tags))

        return claim
