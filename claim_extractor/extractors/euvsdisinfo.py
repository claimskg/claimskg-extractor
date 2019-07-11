# -*- coding: utf-8 -*-
import re
from typing import List, Set

from bs4 import BeautifulSoup
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching, find_by_text

from datetime import datetime


class EuvsdisinfoFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def retrieve_listing_page_urls(self) -> List[str]:
        data = caching.get('https://euvsdisinfo.eu/disinformation-cases')
        soup = BeautifulSoup(data, 'html.parser')
        nb = self.find_page_count(soup)
        links = []
        for x in range(0, int(nb/10)):
            links.append('https://euvsdisinfo.eu/disinformation-cases/?offset='+str(x*10))
        return links

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        a = parsed_listing_page.find('a', {'class':'disinfo-db-next last'})
        page_re = re.compile("\?offset=([0-9]+)")
        max_page = int(page_re.match(a['href']).group(1))
        return max_page

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) -> Set[str]:
        urls = []
        elems = parsed_listing_page.findAll('div', {'class':'disinfo-db-post'})
        for elem in elems:
            url = elem.find('a')
            urls.append(url['href'])
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claim = Claim()
        claim.set_url(url)
        claim.set_source("euvsdisinfo")

        claim_str = parsed_claim_review_page.find('div', {'class':'report-summary-text'}).text
        claim.set_claim(claim_str)

        divs = parsed_claim_review_page.findAll('div', {'class':'report-disinfo-link'})
        urls = []
        for div in divs:
            try:
                url = div.find('a')['href']
                urls.append (url)
            except Exception as e:
                pass

        claim.set_refered_links(urls)

        divs = parsed_claim_review_page.findAll('div', {'class':'report-meta-item'})

        for div in divs:
            elem = div.find('span')
            if div.find(string=re.compile("Date")):
                claim.setDatePublished(elem.text)
            elif div.find(string=re.compile("Keywords")):
                claim.set_tags(elem.text)
            elif div.find(string=re.compile("Outlet")):
                claim.set_author(elem.text)

        title = parsed_claim_review_page.find('h2', {'class':'report-title section_title'}).text
        claim.set_title(title)

        body = parsed_claim_review_page.find('div', {'class':'report-disproof-text'}).text
        claim.setBody(body)

        x = parsed_claim_review_page.find('div', {'class':'report-disproof-title'}).text

        if x == 'Disproof':
            claim.set_alternate_name('false')

        return [claim]