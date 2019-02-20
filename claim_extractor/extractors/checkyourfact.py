# -*- coding: utf-8 -*-

from typing import List, Set

from bs4 import BeautifulSoup
from dateparser.search import search_dates
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


class FactscanFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

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
        else:
            count -= 1

        return count

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> Set[str]:
        urls = self.extract_urls(parsed_listing_page)

        for page_number in tqdm(range(2, number_of_pages)):
            url = "https://checkyourfact.com/page/" + page_number + "/"
            page = caching.get(url, headers=self.headers, timeout=5)
            if page:
                current_parsed_listing_page = BeautifulSoup(page, "lxml")
                urls = set.union(urls, self.extract_urls(current_parsed_listing_page))
            else:
                break

        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = set()
        links = parsed_listing_page.find('articles').findAll('a', href=True)
        for anchor in links:
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
        claim.setSource("checkyourfact")

        # title
        title = parsed_claim_review_page.find('article').find("h1")
        claim.setTitle(title.text.replace("FACT CHECK: ", ""))

        date_str = search_dates(url.replace("http://dailycaller.com/", "").replace("/", " "),
                                settings={'DATE_ORDER': 'YMD'})[0][1].strftime("%Y-%m-%d")
        claim.setDate(date_str)

        # body
        body = parsed_claim_review_page.find("article")
        claim.setBody(body.get_text())

        # related links
        div_tag = parsed_claim_review_page.find("article")
        related_links = []
        for link in div_tag.findAll('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        claim.setClaim(claim.title)

        tags = []

        for tag in parsed_claim_review_page.findAll('meta', {"property": "article:tag"}):
            tags.append(tag["content"])
        claim.set_tags(", ".join(tags))

        return claim
