# -*- coding: utf-8 -*-
import re
from typing import List, Set

from bs4 import BeautifulSoup
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching, find_by_text

import json

# factutel.afp.com can be changed by the english version factcheck.afp.com which contains much more claims

class AfpfactuelFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def retrieve_listing_page_urls(self) -> List[str]:
        last = self.find_last_page()
        tab = []
        print(last)
        for i in range(1,10):
            tab.append('https://factuel.afp.com/?page='+str(i))
        return tab

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        return None
    
    def find_last_page(self): #returns last page listing articles
        page = 80 #86
        count = 32
        lim = -1
        #Dichotomy
        while count >= 1:
            url = "https://factuel.afp.com/?page=" + str(int(page))
            result = caching.get(url, headers=self.headers, timeout=10)
            parsed = BeautifulSoup(result, self.configuration.parser_engine)
            article = parsed.findAll("article")
            if lim > 0:
                count = count/2
            if(len(article) != 0) :
                if count < 1:
                    return int(page)
                page = page + count
            else:
                if lim == -1:
                    lim = page
                    count = count/2
                elif count < 1:
                    return int(page-1)
                page = page - count


    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) -> List[str]:
        urls = []
        links = parsed_listing_page.findAll('article')
        for link in links:
            url = link.find('a')['href']
            urls.append("https://factuel.afp.com"+url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claim = Claim()

        data = parsed_claim_review_page.find(string=re.compile("schema.org"))
        data = json.loads(str(data))

        try:
            author = data['@graph'][0]['itemReviewed']['author']
            claim_str = data['@graph'][0]['claimReviewed']
            if len(str(author['name'])) == 0:
                return []
            claim.set_author(author['name'])
        except Exception as e:
            return []

        try:
            rating = data['@graph'][0]['reviewRating']
            claim.set_alternate_name(rating['alternateName'])
        except Exception as e:
            pass

        try:
            claim.set_best_rating(rating['bestRating'])
            claim.setWorstRating(rating['worstRating'])
            claim.set_rating_value(rating['ratingValue'])
        except Exception as e:
            pass

        claim.set_url(url)
        claim.set_source("factuel_afp")

        try:
            title = data['@graph'][0]['name']
            claim.set_title(title)
        except Exception as e:
            pass

        claim.set_claim(claim_str)

        try:
            claim.setDate(data['@graph'][0]['itemReviewed']['datePublished'])
        except Exception as e:
            pass

        try:
            date = data['@graph'][0]['datePublished']
            claim.setDatePublished(date.split(' ')[0])
        except Exception as e:
            pass


        body = parsed_claim_review_page.find('div', {'class':'article-entry clearfix'})
        claim.setBody(body.text)

        links = []
        children = parsed_claim_review_page.find('div', {'class':'article-entry clearfix'}).children
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