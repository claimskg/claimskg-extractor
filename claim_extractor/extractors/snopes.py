# -*- coding: utf-8 -*-
import re
from typing import List

import dateparser
from bs4 import BeautifulSoup
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


class DummyTag(object):
    def __init__(self):
        self.text = ""


url_blacklist = ["https://www.snopes.com/fact-check/24731-2/"]


class SnopesFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def retrieve_listing_page_urls(self) -> List[str]:
        return ["https://www.snopes.com/fact-check/"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        #next_link = parsed_listing_page.find("a", {"class", "btn-next btn"})['href']
        next_link = parsed_listing_page.find("a", {"class", "page-link font-weight-bold"})['href']
        next_page_contents = caching.get(next_link, headers=self.headers, timeout=5)
        next_page = BeautifulSoup(next_page_contents, "lxml")

        title_text = next_page.find("title").text  # Format u'Fact Checks Archive | Page 2 of 1069 | Snopes.com'
        max_page_pattern = re.compile("Page [0-9]+ of ([0-9+]+)")
        result = max_page_pattern.match(title_text.split("|")[1].strip())
        max_page = int(result.group(1))
        #max_page = int("150")

        return max_page
        
    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = self.extract_urls(parsed_listing_page)
        for page_number in tqdm(range(2, number_of_pages)):
            if 0 < self.configuration.maxClaims < len(urls):
                break
            url = listing_page_url + "page/" + str(page_number)
            page = caching.get(url, headers=self.headers, timeout=5)
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls = urls + self.extract_urls(current_parsed_listing_page)
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = list()
        links = parsed_listing_page.findAll("article", {"class": "media"})
        
        for anchor in links:
            anchor = anchor.find('a', href=True)
            url = str(anchor['href'])
            max_claims = self.configuration.maxClaims
            if 0 < max_claims <= len(urls):
                break
            if url not in self.configuration.avoid_urls:
                urls.append(url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        if url in url_blacklist:
            return []
        claim = Claim()

        # url
        claim.set_url( url )

        # souce
        claim.set_source( "snopes" )

        # title
        title = None
        if parsed_claim_review_page.select( 'article > header > h1' ):
            for tmp in parsed_claim_review_page.select( 'article > header > h1' ):
                title = tmp.text.strip()
            sub_title = parsed_claim_review_page.select( 'article > header > h2' )
            claim.set_title( title.strip() )

        # author 
        author_list = []
        author_links = []
        if parsed_claim_review_page.select( 'article > header > ul.list-unstyled.authors.list-unstyled.d-flex.flex-wrap.comma-separated > li > a' ):
            for author_a in parsed_claim_review_page.select( 'article > header > ul.list-unstyled.authors.list-unstyled.d-flex.flex-wrap.comma-separated > li > a' ):
                if hasattr( author_a, 'href' ):
                    author_list.append( author_a.text.strip() )
                    author_links.append( author_a.attrs['href'] )
                else:
                    print( "no author?" )
                
        claim.set_author( ", ".join( author_list ) )
        claim.author_url = ( ", ".join( author_links ) )

        # date
        datePub = None
        dateUpd = None
        date_str = ""
        date_ = parsed_claim_review_page.find( 'ul', { "class": "dates" } )
       
        if date_:
            dates=date_.find( 'li', { "class": "font-weight-bold text-muted" } )
            dateSpans = dates.span
            for dateItems in dateSpans:
                if dateItems == 'Published':
                    datePub = dateItems.next.strip()
                    date_str = dateparser.parse( datePub ).strftime( "%Y-%m-%d" )
                    claim.set_date_published( date_str )
                    claim.set_date( date_str ) 
                if dateItems == 'Updated': 
                    dateUpd = dateItems.next.strip()
                    date_str = dateparser.parse( dateUpd ).strftime( "%Y-%m-%d" )
                    claim.set_date( date_str )

        # claim image?
        # -
        
        # claim
        claim_text = None
        if parsed_claim_review_page.select( 'article > div > div.claim-text.card-body' ):
            for p in parsed_claim_review_page.select( 'article > div > div.claim-text.card-body' ):
                if hasattr(p, 'text' ):
                    claim_text = p.text.strip()
            claim.set_claim( claim_text )

        # rating -> https://www.snopes.com/fact-check-ratings/
        rating = None
        if parsed_claim_review_page.select( 'article > div > div > div > div.media-body > span' ):
            for rating_span in parsed_claim_review_page.select( 'article > div > div > div > div.media-body > span' ):
                rating = rating_span.text.strip()
            claim.set_rating( rating )
        # claim.set_rating_value( rating )

        # rating best
        whats_true = None
        if parsed_claim_review_page.select( 'article > div > div > div.whats-true > div > p' ):
            for rating_span_true in parsed_claim_review_page.select( 'article > div > div > div.whats-true > div > p' ):
                whats_true = rating_span_true.text.strip()
            claim.set_best_rating( whats_true )

        # rating wors
        whats_true = False
        if parsed_claim_review_page.select( 'article > div > div > div.whats-false > div > p'):
            for rating_span_false in parsed_claim_review_page.select( 'article > div > div > div.whats-false > div > p' ):
                whats_false = rating_span_false.text.strip()
            claim.setWorstRating( whats_false )

        # rating Undetermined?
        whats_undetermined = False
        if parsed_claim_review_page.select( 'article > div > div > div.whats-undetermined > div > p'):
            for rating_span_undetermined in parsed_claim_review_page.select( 'article > div > div > div.whats-undetermined > div > p' ):
                whats_undetermined = rating_span_undetermined.text.strip()
            claim.set( whats_undeterminede )

        # Body descriptioon
        text = ""
        if parsed_claim_review_page.select( 'article > div.single-body.card.card-body.rich-text > p' ):
            for child in parsed_claim_review_page.select( 'article > div.single-body.card.card-body.rich-text > p' ):
                text += " " + child.text
            body_description = text.strip()
            claim.set_body( body_description )

        # related links
        related_links = []
        if parsed_claim_review_page.select( 'article > div.single-body.card.card-body > p > a' ):
            for link in parsed_claim_review_page.select( 'article > div.single-body.card.card-body > p > a' ):
                if hasattr( link, 'href' ):
                    related_links.append( link['href'] )
            claim.set_refered_links( related_links )
                
        # tags
        tags = []
        if parsed_claim_review_page.select( 'article > footer > div > a > div > div' ):
            for tag in parsed_claim_review_page.select( 'article > footer > div > a > div > div' ): 
                if hasattr( tag, 'text' ):
                    tags.append( tag.text.strip() )
            claim.set_tags( ", ".join( tags ) )
                
        #  No Rating? No Claim? 
        if not claim_text or not rating:
            print( url )
            if not rating: 
                print ( "-> Rating cannot be found!" )
            if not claim_text: 
                print ( "-> Claim cannot be found!" )
            return []
        
        return [claim]