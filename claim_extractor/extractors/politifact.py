# -*- coding: utf-8 -*-
import re
from typing import List, Set

from bs4 import BeautifulSoup
from dateparser.search import search_dates
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching
from ast import parse


class PolitifactFactCheckingSiteExtractor(FactCheckingSiteExtractor):
    
    def __init__(self, configuration: Configuration):
        super().__init__(configuration)
        
    def retrieve_listing_page_urls(self) -> List[str]:
        return ['https://www.politifact.com/factchecks/list']
    
    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        max_page = 1000
        return max_page
    
    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = self.extract_urls(parsed_listing_page)
        for page_number in tqdm(range(2, number_of_pages)):
            url = listing_page_url + "?page=" + str(page_number)
            page = caching.get(url, headers=self.headers, timeout=5)
            if not page:
                break
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls += self.extract_urls(current_parsed_listing_page)
        return urls
    
    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = list()
        links = parsed_listing_page.findAll("article", {"class": "m-statement"})
        for link in links:
            link_quote=link.find("div", {"class": "m-statement__quote"})
            link = link_quote.find('a',  href=True)
            url = "http://www.politifact.com" + str(link['href'])
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
        title = parsed_claim_review_page.find("h2", {"class": "c-title"})
        claim.set_title(title.text)
        
        # date
        date = parsed_claim_review_page.find('span', {"class": "m-author__date"})
        if date:
            date_str = search_dates(date.text)[0][1].strftime("%Y-%m-%d")
            claim.set_date(date_str)

        # rating
        statement_body=parsed_claim_review_page.find("div", {"class", "m-statement__body"})
        statement_detail = statement_body.find("div", {"class", "c-image"})
        statement_detail_image=statement_detail.find("picture")
        statement_detail_image_alt=statement_detail_image.find("img",{"class", "c-image__original"})
        if statement_detail_image_alt:
            claim.alternate_name = statement_detail_image_alt['alt']

        # body
        body = parsed_claim_review_page.find("article", {"class": "m-textblock"})
        claim.set_body(body.get_text())

        # author
        statement_meta = parsed_claim_review_page.find("div", {"class": "m-statement__meta"})
        if statement_meta:
            author = statement_meta.find("a").text
            claim.set_author(author)

        # date published
        if statement_meta:
            meta_text = statement_meta.text
            if "on" in meta_text:
                meta_text = meta_text.split(" on ")[1]
            if "in" in meta_text:
                meta_text = meta_text.split(" in ")[0]
            if meta_text:
                date = search_dates(meta_text)
                if date:
                    date = date[0][1].strftime("%Y-%m-%d")
                    claim.setDatePublished(date)
        
        # related links
        div_tag = parsed_claim_review_page.find("article", {"class": "m-textblock"})
        related_links = []
        for link in div_tag.findAll('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        claim.set_claim(parsed_claim_review_page.find("div", {"class": "m-statement__quote"}).text.strip())
        
        tags = []
        ul_tag = parsed_claim_review_page.find("ul", {"class", "m-list"})
        if ul_tag:
            ul_tag_contents = ul_tag.findAll("li", {"class", "m-list__item"})
            for a in ul_tag_contents:
                a_tag=a.find("a", title=True)
                a_tag_text=a_tag['title']
                tags.append(a_tag_text)

            claim.set_tags(",".join(tags))

        return [claim]





