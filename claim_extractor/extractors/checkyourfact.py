# -*- coding: utf-8 -*-
import re
from typing import List

from bs4 import BeautifulSoup
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching, find_by_text


class CheckyourfactFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)
        self.date_regexp = re.compile("^([0-9]{4})/([0-9]{2})/([0-9]{2})*")

    def retrieve_listing_page_urls(self) -> List[str]:
        return ["https://checkyourfact.com/page/1/"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        count = 26
        url = "https://checkyourfact.com/page/" + str(count + 1)
        result = caching.get(url, headers=self.headers, timeout=10)
        if result:
            while result:
                count += 1
                url = "https://checkyourfact.com/page/" + str(count)
                result = caching.get(url, headers=self.headers, timeout=10)
                if result:
                    parsed = BeautifulSoup(result, self.configuration.parser_engine)
                    articles = parsed.find("articles").findAll("article")
                    if not articles or len(articles) == 0:
                        break
        else:
            count -= 1

        return count

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = self.extract_urls(parsed_listing_page)

        for page_number in tqdm(range(2, number_of_pages)):
            url = "https://checkyourfact.com/page/" + str(page_number) + "/"
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
            claim.set_alternate_name(rating_text)
        else:
            pass

        tags = []

        for tag in parsed_claim_review_page.findAll('meta', {"property": "article:tag"}):
            tags.append(tag["content"])
        claim.set_tags(", ".join(tags))
        if len(claim.alternate_name) == 0:
            return []
        else:
            return [claim]
