# -*- coding: utf-8 -*-
import json
import re
from typing import List

from bs4 import BeautifulSoup
from tqdm import trange

from claim_extractor import Claim
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


# factutel.afp.com can be changed by the english version factcheck.afp.com which contains much more claims

class AfpfactuelFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def retrieve_listing_page_urls(self) -> List[str]:
        return ['https://factuel.afp.com/']

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        return self.find_last_page()

    def find_last_page(self):  # returns last page listing articles
        page = 80  # 86
        count = 32
        lim = -1
        # Dichotomy
        while count >= 1:
            url = "https://factuel.afp.com/?page=" + str(int(page))
            result = caching.get(url, headers=self.headers, timeout=10)
            parsed = BeautifulSoup(result, self.configuration.parser_engine)
            article = parsed.findAll("article")
            if lim > 0:
                count = count / 2
            if len(article) != 0:
                if count < 1:
                    return int(page)
                page = page + count
            else:
                if lim == -1:
                    lim = page
                    count = count / 2
                elif count < 1:
                    return int(page - 1)
                page = page - count

    def extract_urls(self, parsed_listing_page):
        urls = list()
        links = parsed_listing_page.findAll('article')
        for link in links:
            url = link.find('a')['href']
            urls.append("https://factuel.afp.com" + url)
        return urls

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) -> List[
        str]:
        urls = self.extract_urls(parsed_listing_page)
        for page_number in trange(2, number_of_pages):
            url = "https://factuel.afp.com/?page=" + str(int(page_number))
            page = caching.get(url, headers=self.headers, timeout=20)
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls += self.extract_urls(current_parsed_listing_page)

        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claim = Claim()

        data = parsed_claim_review_page.find(string=re.compile("schema.org"))
        data = json.loads(str(data))

        node_zero = data['@graph'][0]

        if node_zero and 'claimReviewed' in node_zero.keys():
            claim_str = node_zero['claimReviewed']
            if claim_str and len(claim_str) > 0:
                claim.set_claim(claim_str)
            else:
                return []

        rating = data['@graph'][0]['reviewRating']
        if rating and 'alternateName' in rating.keys():
            claim.set_alternate_name(rating['alternateName'])
            try:
                claim.set_best_rating(rating['bestRating'])
                claim.setWorstRating(rating['worstRating'])
                claim.set_rating_value(rating['ratingValue'])
            except Exception:
                pass
        else:
            return []

        if 'author' in data['@graph'][0]['itemReviewed'].keys():
            author = data['@graph'][0]['itemReviewed']['author']
            if author and 'name' in author.keys():
                if len(str(author['name'])) > 0:
                    claim.set_author(author['name'])

        claim.set_url(url)
        claim.set_source("factuel_afp_fr")

        try:
            title = data['@graph'][0]['name']
            claim.set_title(title)
        except Exception:
            pass

        try:
            claim.set_date(data['@graph'][0]['itemReviewed']['datePublished'])
        except Exception:
            pass

        try:
            date = data['@graph'][0]['datePublished']
            claim.set_date_published(date.split(' ')[0])
        except Exception:
            pass

        body = parsed_claim_review_page.find('div', {'class': 'article-entry clearfix'})
        claim.set_body(body.text)

        links = []
        children = parsed_claim_review_page.find('div', {'class': 'article-entry clearfix'}).children
        for child in children:
            try:
                if child.name == 'aside':
                    continue
                elems = child.findAll('a')
                for elem in elems:
                    links.append(elem['href'])
            except Exception as e:
                continue
        claim.set_refered_links(links)

        return [claim]
