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

    def proced_verdict_block(self, url, verdict_strongs, parsed_claim_review_page, updated_position=False, updated_rating_position=0, check_in_other_tags_than_p=False):
        if check_in_other_tags_than_p:
            query_selectors = [".c-article__verdict > ul", ".c-article__verdict > li", ".c-article__verdict > ul > li"]
            for query in query_selectors:
                if parsed_claim_review_page.select(query):                    
                    if updated_position == False: # Try last entry in list (if only one element is given, last == first)
                        rating_position = len(parsed_claim_review_page.select(query))
                    else:  # Yes, go reverse based on rules:
                        rating_position = updated_rating_position
                    break
                else:
                    rating_position = 0
        else:  # Default usecase: Rating located in elements '<p>'
            query = ".c-article__verdict > p"
            if updated_position == False:
                rating_position = len(parsed_claim_review_page.select(query)) - 1  # Penultimate (suspected) position
                if (len(parsed_claim_review_page.select(query)) == 1): # Bugfix: only one entry in list? -> set to position 1
                    rating_position = 1 
            else:
                # Updated position based on rules (n) -1
                rating_position = updated_rating_position


        # tmp_position != Position:
        # p[0] == Position 1
        # p[n] == Position n-1        
        tmp_position = int(0)
        tmp_verdict = ""

        # Extract rating:
        # New method: Get better result exctracting rating on suspected position
        if parsed_claim_review_page.select(query):
            for p in parsed_claim_review_page.select(query):
                tmp_position += 1
                if (tmp_position == rating_position):
                    if hasattr(p, 'text'):
                        verdict = str(p.text.strip())
                        if "–" or u"\u002d" or u"\u2013" in verdict:
                            split_text = verdict.split(u"\u2013")
                            if len(split_text) > 1:
                                verdict = split_text[0].strip()
                            else:
                                split_text = verdict.split(u"\u002d")
                                if len(split_text) > 1:
                                    verdict = split_text[0].strip()
                                else:
                                    split_text = verdict.split("-")
                                    if len(split_text) > 1:
                                        verdict = split_text[0].strip()
                        if (verdict != ""):
                            tmp_verdict = verdict
        elif check_in_other_tags_than_p:
            # Old method: Extract rating over <strong> tag
            for verdict_strong in verdict_strongs:
                if "AAP FactCheck" not in verdict_strong.text and "AAP FactCheck Investigation:" not in verdict_strong.text:
                    tmp_verdict = verdict_strong.text
                    if "-" in tmp_verdict:
                        tmp_verdict = str(tmp_verdict).replace(
                            '–', "").replace(',', "").strip()
                        break
            if (tmp_verdict != ""):
                return tmp_verdict
            else:
                return ""

        # Extract behind "string"?
        if (str("Based on the evidence").lower() in str(tmp_verdict).lower()
        or str("Based on this evidence").lower() in str(tmp_verdict).lower()
        or str("Based on the advice").lower() in str(tmp_verdict).lower()
        or str("Based on the above evidence").lower() in str(tmp_verdict).lower()):
            split_text = verdict.split("to be ")
            if len(split_text) > 1:
                split_textt = split_text[1].split(".")
                if len(split_textt) > 1:
                    tmp_verdict = split_textt[0].strip().capitalize()
                else:
                    tmp_verdict = split_text[1].strip().capitalize()
                #print(" " + tmp_verdict + ": " + url)

        # Ruleset - Recall method changing position (as long there are elemtents in the list):
        # 1. If there is some "String" in the verdic rating: update position (n-1)
        if ((str("NOTE:").lower() in str(tmp_verdict).lower()
        or str("AEDT").lower() in str(tmp_verdict).lower()
        or str("Updated").lower() in str(tmp_verdict).lower()
        or str("Published").lower() in str(tmp_verdict).lower()
        or str("*") in str(tmp_verdict).lower()
        or u"\u002a" in str(tmp_verdict).lower()
        or str("AAP FactCheck is an accredited member").lower() in str(tmp_verdict).lower()
        or (rating_position > 1 and tmp_verdict == "")) # Bugfix: sometimes there are empty entrys: skipt it!
        and (str("Based on the evidence").lower() not in str(tmp_verdict).lower())
        and (str("Based on this evidence").lower() not in str(tmp_verdict).lower())  
        and (str("Based on the advice").lower() not in str(tmp_verdict).lower())
        and (str("Based on the above evidence").lower() not in str(tmp_verdict).lower())          
        and (check_in_other_tags_than_p == False)):            
            tmp_rating_position = rating_position - 1
            if (tmp_rating_position >= 0):
                if check_in_other_tags_than_p:
                    print(" Need ongoing reverse (check_in_other_tags_than_p) ?" + url)
                    # tmp_verdict = self.proced_verdict_block(url, verdict_strongs, parsed_claim_review_page, True, tmp_rating_position, True)
                else:    
                    tmp_verdict = self.proced_verdict_block(url, verdict_strongs, parsed_claim_review_page, True, tmp_rating_position, False)

        # 2. If verdic (rating) still empty or more than 3 words -> proceed other tags than <p>
        if (tmp_verdict == "" or len(str(tmp_verdict).split()) > 3) and check_in_other_tags_than_p == False:
            tmp_verdict = self.proced_verdict_block(url, verdict_strongs, parsed_claim_review_page, False, 0, True)

        return tmp_verdict

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

        verdict = self.proced_verdict_block(url, verdict_strongs, parsed_claim_review_page)
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
