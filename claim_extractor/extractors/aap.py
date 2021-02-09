# -*- coding: utf-8 -*-
import json
from typing import List

import dateparser
from bs4 import BeautifulSoup

from claim_extractor import Claim
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


class AapFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def retrieve_listing_page_urls(self) -> List[str]:
        return ['https://factcheck.aap.com.au/']

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        return 1

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = []
        offset = 1
        links = caching.get(f"https://loadmore.aap.com.au/category?category=6&postOffset={offset}&perPage=100")
        offset = 100
        while links != "[]":
            parsed_json = json.loads(links)
            for link in parsed_json:
                urls.append(link['link'])
            links = caching.get(f"https://loadmore.aap.com.au/category?category=6&postOffset={offset}&perPage=100")
            offset += 100
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claim = Claim()
        claim.set_url(url)
        claim.set_source("factcheck_aap")

        # The title
        elements = parsed_claim_review_page.findAll('h1')
        if len(elements) == 1:
            title = elements[0].text
        else:
            title = elements[1].text

        claim.set_title(title.strip())

        body = parsed_claim_review_page.select(".c-article__content")

        verdict_div = body[0].select(".c-article__verdict")
        if len(verdict_div) > 0:
            verdict_strongs = verdict_div[0].find_all("strong")
        else:
            verdict_strongs = body[0].find_all("strong")
        verdict = ""
        for verdict_strong in verdict_strongs:
            if "AAP FactCheck" not in verdict_strong.text and "AAP FactCheck Investigation:" not in verdict_strong.text:
                verdict = verdict_strong.text
                break
        claim.set_rating(verdict)
        if len(verdict_div) > 0:
            verdict_div[0].decompose()

        # The body
        body_text = body[0].text
        claim.set_body(body_text)

        # Date where the article was published

        date_tag = parsed_claim_review_page.find("date", attrs={'class': 'd-none'})
        date_text = date_tag.text
        find_date = dateparser.parse(date_text)
        claim.set_date_published(find_date.strftime("%Y-%m-%d"))

        elements = body[0].find_all('a')
        refs = []
        for elem in elements:
            refs.append(elem['href'])
        claim.set_refered_links(refs)

        return [claim]
