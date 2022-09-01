# -*- coding: utf-8 -*-
import json
import re
from typing import List

from bs4 import BeautifulSoup
from tqdm import trange

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


# factutel.afp.com can be changed by the english version factcheck.afp.com which contains much more claims

class AfpfactcheckFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration = Configuration(), ignore_urls: List[str] = None, headers=None,
                 language="eng"):
        super().__init__(configuration, ignore_urls, headers, language)
        self.base_url = "https://factcheck.afp.com"

    def retrieve_listing_page_urls(self) -> List[str]:
        return ["https://factcheck.afp.com/list/all/37881/all/all/79",
                "https://factcheck.afp.com/list/all/37075/all/all/80",
                "https://factcheck.afp.com/list/all/37783/all/all/81",
                "https://factcheck.afp.com/list/all/37074/all/all/82",
                "https://factcheck.afp.com/list/all/all/39405/all/2526",
                "https://factcheck.afp.com/list/all/all/39289/all/2387",
                "https://factcheck.afp.com/list/all/all/35799/all/86",
                "https://factcheck.afp.com/list/all/all/38628/all/446",
                "https://factcheck.afp.com/list/all/all/all/38558/19",
                "https://factcheck.afp.com/list/all/all/all/38561/22",
                "https://factcheck.afp.com/list/all/all/all/38560/20",
                "https://factcheck.afp.com/list/all/all/all/38562/17",
                "https://factcheck.afp.com/list/all/all/all/38559/21",
                "https://factcheck.afp.com/list/all/all/all/38563/285"
                ]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        paginaltion_nav = parsed_listing_page.find("nav", attrs={'id': 'pagination'})
        #print(paginaltion_nav)
        last_li_href = list(paginaltion_nav.select(".page-link-desktop"))[-1]['href']
        page_matcher = re.match("^.*page=([0-9]+)$", last_li_href)
        last_page_number = page_matcher.group(1)
       
        return int(last_page_number)

    def extract_urls(self, parsed_listing_page):
        urls = list()
        featured_post = parsed_listing_page.find('div', attrs={'class': 'featured-post'})
        if featured_post is None:
            featured_post = parsed_listing_page.find('main')
        cards = featured_post.select(".card")
        for card in cards:
            url = card.find("a")['href']
            urls.append(self.base_url + url)
       
        return urls

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) -> List[
        str]:
        urls = self.extract_urls(parsed_listing_page)
        
        for page_number in trange(1, number_of_pages):
            #if ((page_number*15) + 14 >= self.configuration.maxClaims):
                #break
            url = listing_page_url + "?page=" + str(int(page_number))
            
            page = caching.get(url, headers=self.headers, timeout=20)
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls += self.extract_urls(current_parsed_listing_page)
        #print(urls)
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
            claim.set_rating(rating['alternateName'])
            try:
                claim.set_best_rating(rating['bestRating'])
                claim.set_worst_rating(rating['worstRating'])
                claim.set_rating_value(rating['ratingValue'])
            except Exception:
                pass
        else:
            return []

        if 'author' in data['@graph'][0]['itemReviewed'].keys():
            author = data['@graph'][0]['itemReviewed']['author']
            if author and 'name' in author.keys():
                if len(str(author['name'])) > 0:
                     #changes .........................
                   
                    if type(author['name']) is list:
                        claim.set_author(author['name'][0])
                        
                    else:
                        claim.set_author(author['name'])

        claim.set_url(url)
        claim.set_source("factcheck_afp")

        try:
            title = data['@graph'][0]['name']
            claim.set_title(title)
        except Exception:
            pass

        try:
            claim.set_date(data['@graph'][0]['itemReviewed']['datePublished'])
        except Exception:
            pass
        except KeyError:
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
                if (child != "\n" and not " " ):
                    elems = child.findAll('a')
                    for elem in elems:
                        links.append(elem['href'])
            except Exception as e:
                continue
        claim.set_refered_links(links)
        
        return [claim]
