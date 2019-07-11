# -*- coding: utf-8 -*-
import re
from typing import List, Set

from bs4 import BeautifulSoup
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching, find_by_text

from datetime import datetime, timedelta

class FullfactFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def get_links(self) :
        today = datetime.today()
        d = ldate = today
        lim = datetime.strptime('2019-06-01', "%Y-%m-%d") # Date where the script will stop the scraping
        i = 0
        delta = timedelta(days=3)
        urls = set()
        while d > lim :
            i = i+1
            url = 'http://web.archive.org/web/'+d.strftime('%Y%m%d')+'/https://fullfact.org/'

            r = caching.head(url, headers=self.headers, timeout=10)

            try:
                if r['status_code'] != 200:
                    d = d - delta
                    continue

                dre = re.compile("http://web.archive.org/web/([0-9]+)/https://fullfact.org/")
                date = dre.match(r['url']).group(1) # date of the link that is being processed
                date = datetime.strptime(date[:8], "%Y%m%d")

                if (date.day == ldate.day and date.month == ldate.month):
                    print(date.strftime('%Y-%m-%d'))
                    d = d - delta # d is a date that discrements by a day each 
                    continue
            except Exception as e:
                d = d - delta
                continue

            print('Added home page of '+date.strftime('%Y-%m-%d'))
            urls.add(r['url'])
            ldate = date # ldate is the date of the last link that was added
            d = date - delta

        return urls

    def retrieve_listing_page_urls(self) -> List[str]:
        return self.get_links()

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        return None

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) -> Set[str]:
        urls = []
        div = parsed_listing_page.find('div', id='mostRecent')
        elems = div.findAll('li')
        for elem in elems:
            url = elem.find('a')['href'][20:]
            n = len(self.seen)
            self.seen.add(url)
            if(len(self.seen) == n):
                continue
            urls.append(url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claims = []

        ol = parsed_claim_review_page.find('ol', {'class': 'breadcrumb col-xs-12'})
        elems = ol.findAll('a')
        keywords = []
        for elem in elems:
            keywords.append(elem.text)


        #extraction of brief claims
        d = parsed_claim_review_page.findAll('div', {"id":"briefClaimConclusion"})
        if len(d) != 0 :
            d = d[0].find('div', {"class":"box-panel"})
            divs = d.children
            for div in divs:
                if(type(div) == type(d) and div.name == 'div'):
                    try:
                        claim = Claim()
                        claim.set_url(url)
                        claim.set_source("fullfact")
                        claim_str = div.find('div', {"class": "col-xs-12 col-sm-6 col-left"}).find('p').text
                        conclusion = div.find('div', {"class": "col-xs-12 col-sm-6 col-right"}).find('p').text

                        claim.set_claim(claim_str)
                        claim.set_alternate_name(conclusion)
                        claim.set_tags(','.join(keywords))
                        claims.append(claim)
                    except Exception as e:
                        continue

        #Extraction of quotes
        quotes = parsed_claim_review_page.findAll('blockquote')

        if(len(claims) == 0 or len(quotes) == 0):
            return claims

        for quote in quotes:            
            claim = Claim()
            claim.set_url(url)
            claim.set_source("fullfact")
            try:
                p = quote.findAll('p')

                if(len(p) == 1): # if there one paragraph then there is no author nor date
                    claim.set_claim(p[0].text)
                    claim.set_tags(','.join(keywords))
                    claims.append(claim)
                    continue

                claim_str = ''
                for x in p[:-1]: # Sometimes the quotes is made of 2 paragraphes or more
                    claim_str = x.text

                if(len(claim_str) < 4): # if it's too small it is not a claim
                    continue

                p = p[-1] #last paragraph always mentions the author and the date
                author = p.text.split(',')[:-1] #and there is always a semicolon seperating the two
                date = p.text.split(',')[-1]

                while not claim_str[0].isalnum():
                    claim_str = claim_str[1:]
                
                while not claim_str[-1].isalnum():
                    claim_str = claim_str[:-1]

                claim.set_claim(claim_str)
                claim.set_author(''.join(author))
            except Exception as e:
                continue

            try: 
                a = p.find('a') #usually the date is mentionned with the link where the claim was said
                d = datetime.strptime(a.text, '%d %B %Y').strftime("%Y-%m-%d")
                claim.set_refered_links(a['href'])
                claim.setDate(d)
            except Exception as e:
                try:
                    d = datetime.strptime(date[1:-1], ' %d %B %Y').strftime("%Y-%m-%d")
                    claim.setDate(d)
                except Exception as e:
                    pass
            claim.set_tags(keywords)
            claims.append(claim)

        return claims
