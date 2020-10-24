# -*- coding: utf-8 -*-
import re
from typing import List

from bs4 import BeautifulSoup, NavigableString, Tag
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


class TruthorfictionFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def retrieve_listing_page_urls(self) -> List[str]:
        return ["https://www.truthorfiction.com/category/fact-checks/"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        page_nav = parsed_listing_page.find("div", {"class": "nav-links"})
        last_page_link = page_nav.findAll("a")[-2]['href']
        page_re = re.compile("https://www.truthorfiction.com/category/fact-checks/page/([0-9]+)/")
        max_page = int(page_re.match(last_page_link).group(1))
        return max_page

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = self.extract_urls(parsed_listing_page)
        for page_number in tqdm(range(2, number_of_pages)):
            url = "https://www.truthorfiction.com/category/fact-checks/page/" + str(page_number) + "/"
            page = caching.get(url, headers=self.headers, timeout=20)
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls += self.extract_urls(current_parsed_listing_page)
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = list()
        listing_container = parsed_listing_page.find("div", {"class": "ast-row"})
        titles = listing_container.findAll("h2")
        for title in titles:
            anchor = title.find("a")
            url = str(anchor['href'])
            max_claims = self.configuration.maxClaims
            if 0 < max_claims <= len(urls):
                break
            if url not in self.configuration.avoid_urls:
                urls.append(url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claim = Claim()
        claim.set_url(url)
        claim.set_source("truthorfiction")

        title = parsed_claim_review_page.find("meta", {"property": "og:title"})['content']
        claim.set_title(title)

        article = parsed_claim_review_page.find("article")

        # date

        date_ = parsed_claim_review_page.find('meta', {"property": "article:published_time"})['content']
        if date_:
            date_str = date_.split("T")[0]
            claim.set_date(date_str)

        # body
        content = [tag for tag in article.contents if not isinstance(tag, NavigableString)]
        body = content[-1]  # type: Tag
        if body.has_attr("class") and "content-source" in body['class']:
            body = content[-2]
        claim.set_body(body.text.strip())

        # related links
        related_links = []
        for link in body.findAll('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        description = article.find("div", {"class", "claim-description"})
        rating = article.find("div", {"class", "rating-description"})

        if description and rating:
            claim.set_claim(description.text)
            claim.alternate_name = rating.text
        else:
            h1 = article.find("h1")
            text = h1.text.replace("–", "-")
            split_text = text.split("-")
            rating_text = split_text[-1]
            claim_text = "".join(split_text[0:-1])
            if len(claim_text) == 0 or "-" not in text:
                return []
            else:
                claim.set_alternate_name(rating_text)
                claim.set_claim(claim_text)

        tags = []

        for tag in parsed_claim_review_page.findAll("meta", {"property", "article:tags"}):
            tag_str = tag['content']
            tags.append(tag_str)
        claim.set_tags(", ".join(tags))

        return [claim]
