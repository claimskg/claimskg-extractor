# -*- coding: utf-8 -*-
import re
from datetime import datetime
from typing import List

from bs4 import BeautifulSoup

from claim_extractor import Claim
from claim_extractor.extractors import FactCheckingSiteExtractor


class AapFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def retrieve_listing_page_urls(self) -> List[str]:
        return ['https://factcheck.aap.com.au']

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        return 1

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = []
        links = parsed_listing_page.select('a[href^="/news-media-claims/"]')
        for anchor in links:
            url = "https://factcheck.aap.com.au" + str(anchor['href'])
            max_claims = self.configuration.maxClaims
            urls.append(url)
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

        # The body
        # try:
        children = parsed_claim_review_page.find('div', {"role": "main"}).children
        body = None
        for child in children:
            y = child.find(string=re.compile("The Analysis"))
            if child.name == 'section' and y:
                body = child.text
        if body and len(body) > 0:
            claim.set_body(body)
        # except Exception as e:
        #     pass

        # Claim
        x = parsed_claim_review_page.find(string=re.compile("The Statement")).parent
        while str(x.name) != 'h2':
            x = x.parent

        x = x.next_sibling
        claim_str = ''
        while str(x.name) != 'h2':
            y = x.find('strong')
            if (y):
                claim_str = y.text
                if not y.text[0].isalnum():
                    claim_str = claim_str[1:]
                if not y.text[-1].isalnum():
                    claim_str = claim_str[:-1]
                claim.set_claim(claim_str)
                break
            x = x.next_sibling

        if claim_str == '':
            return []

        claim.set_claim(x.text[1:-1])

        # Set the date where the claim was first said
        y = x.next_sibling
        x = y.text.split(' ')

        while y.name != 'h2':
            while x[-1] == '':
                x = x[:-1]

            n = 10
            while n > 0:
                try:
                    int(x[-1][-1])
                    break
                except Exception as e:
                    x[-1] = x[-1][:-1]
                    n = n - 1
            try:
                claim.set_date(datetime.strptime(x[-3] + ' ' + x[-2] + x[-1], '%B %d,%Y').strftime("%Y-%m-%d"))
                claim.set_author(' '.join(x[:-3]))
                break
            except Exception as e:
                y = y.next_sibling
                x = y.text.split(' ')

        # Date where the article was published
        x = parsed_claim_review_page.find(string=re.compile("First published")).split(' ')
        x = datetime.strptime(x[2] + ' ' + x[3] + x[4], '%B %d,%Y').strftime("%Y-%m-%d")
        claim.setDatePublished(x)

        # Truth value
        x = parsed_claim_review_page.find(string=re.compile("The Verdict")).parent.parent.next_sibling

        claim.set_alternate_name(x.find('strong').text.replace("-", "".replace("–", "").strip()))

        # References
        x = parsed_claim_review_page.find(string=re.compile("The References")).parent
        while str(x.name) != 'h2':
            x = x.parent
        x = x.parent

        elements = x.findAll('a')
        refs = []
        for elem in elements:
            refs.append(elem['href'])
        claim.set_refered_links(refs)

        return [claim]
