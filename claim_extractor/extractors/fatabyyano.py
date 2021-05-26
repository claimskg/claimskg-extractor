# -*- coding: utf-8 -*-
import json
import math
import re
from typing import *

from bs4 import BeautifulSoup
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


class FatabyyanoFactCheckingSiteExtractor(FactCheckingSiteExtractor):
    # Constants

    def __init__(self, configuration: Configuration):
        super().__init__(configuration, language="ara")

    def get(self, url):
        """ @return the webpage """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
        html = caching.get(url, headers=headers)
        soup = BeautifulSoup(html, 'lxml')
        # removing some useless tags
        for s in soup.select("script, iframe, head, header, footer, style"):
            s.extract()
        return soup

    def retrieve_listing_page_urls(self) -> List[str]:
        """
            Abstract method. Retrieve the URLs of pages that allow access to a paginated list of claim reviews. This
            concerns some sites where all the claims are not listed from a single point of access but first
            categorized by another criterion (e.g. on politifact there is a separate listing for each possible rating).
            :return: Return a list of listing page urls
        """
        return ["https://fatabyyano.net/newsface/0/"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        """
            A listing page is paginated and will sometimes contain information pertaining to the maximum number of pages
            there are. For sites that do not have that information, please return a negative integer or None
            :param parsed_listing_page:
            :return: The page count if relevant, otherwise None or a negative integer
        """
        page_numbers = parsed_listing_page.select(
            "div.nav-links a.page-numbers span")
        maximum = 1
        for page_number in page_numbers:
            if page_number.text != "التالي":
                p = int(page_number.text)
                if (p > maximum):
                    maximum = p
        return maximum

    def retrieve_urls(self, parsed_claim_review_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) -> \
            List[str]:
        """
            :parsed_listing_page: --> une page (parsed) qui liste des claims
            :listing_page_url:    --> l'url associé à la page ci-dessus
            :number_of_page:      --> number_of_page
            :return:              --> la liste des url de toutes les claims
        """
        urls = []
        # First single page:
        page_contend = caching.get(listing_page_url, headers=self.headers, timeout=5)
        page = BeautifulSoup(page_contend, "lxml")
        if page is not None:
            for ex_url in self.extract_urls(page):
                urls.append(ex_url)

        # All pages >0:
        for page_number in tqdm(range(2, number_of_pages)):
            if 0 < self.configuration.maxClaims < len(urls):
                break
            url = listing_page_url + "page/" + str(page_number) + "/"
            page_contend = caching.get(url, headers=self.headers, timeout=5)
            page = BeautifulSoup(page_contend, "lxml")
            if page is not None:
                for ex_url in self.extract_urls(page):
                    urls.append(ex_url)
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = list()
        if parsed_listing_page.select( 'div.w-grid-list > article > div > div > a' ):
            for anchor in parsed_listing_page.select( 'div.w-grid-list > article > div > div > a' ):
                if hasattr( anchor, 'href' ):
                    url = anchor.attrs['href']
                max_claims = self.configuration.maxClaims
                if 0 < max_claims <= len(urls):
                    break
                if url not in self.configuration.avoid_urls:
                    urls.append(url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        self.claim = self.extract_claim(parsed_claim_review_page)
        self.review = self.extract_review(parsed_claim_review_page)

        claim = Claim()        
        claim.set_rating_value(
            self.extract_rating_value(parsed_claim_review_page))
        claim.set_rating(self.translate_rating_value(
            self.extract_rating_value(parsed_claim_review_page)))
        claim.set_source("fatabyyano")
        claim.set_author("fatabyyano")
        claim.set_date_published(self.extract_date(parsed_claim_review_page))
        claim.set_claim(self.claim)
        claim.set_body(self.review)
        claim.set_refered_links(self.extract_links(parsed_claim_review_page))
        claim.set_title(self.extract_claim(parsed_claim_review_page))
        claim.set_date(self.extract_date(parsed_claim_review_page))
        claim.set_url(url)
        claim.set_tags(self.extract_tags(parsed_claim_review_page))

        if claim.rating_value != "":
            return [claim]
        else:
            return []

    def is_claim(self, parsed_claim_review_page: BeautifulSoup) -> bool:
        return True

    def extract_claim(self, parsed_claim_review_page: BeautifulSoup) -> str:
        claim = parsed_claim_review_page.select_one("h1.post_title")
        if claim:
            return self.escape(claim.text)
        else:
            # print("something wrong in extracting claim")
            return ""

    def extract_review(self, parsed_claim_review_page: BeautifulSoup) -> str:
        return "" #self.escape(parsed_claim_review_page.select_one("section.l-section.wpb_row.height_small div[itemprop=\"text\"]").text)

    def extract_links(self, parsed_claim_review_page: BeautifulSoup) -> str:
        links = ""
        links_tags = parsed_claim_review_page.select(
            "section.l-section.wpb_row.height_small div[itemprop=\"text\"] a")
        for link_tag in links_tags:
            if link_tag['href']:
                links += link_tag['href'] + ", "
        return links[:len(links) - 1]

    def extract_date(self, parsed_claim_review_page: BeautifulSoup) -> str:
        date = parsed_claim_review_page.select_one(
            "time.w-post-elm.post_date.entry-date.published")
        if date:
            return date['datetime'].split("T")[0]
        else:
            print("something wrong in extracting the date")
            return ""

    def extract_tags(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
            :parsed_claim_review_page:  --> the parsed web page of the claim
            :return:                    --> return a list of tags that are related to the claim
        """
        tags_link = parsed_claim_review_page.select(
            "div.w-post-elm.post_taxonomy.style_simple a[rel=\"tag\"]")
        tags = ""
        for tag_link in tags_link:
            if tag_link.text:
                tag = (tag_link.text).replace("#", "")
                tags += tag + ","

        return tags[:len(tags) - 1]

    def extract_author(self, parsed_claim_review_page: BeautifulSoup) -> str:
        return "fatabyyano"

    def extract_rating_value(self, parsed_claim_review_page: BeautifulSoup) -> str:
        r = ""
        if parsed_claim_review_page.select( 'img' ):
            for img in parsed_claim_review_page.select( 'img' ):
                if hasattr( img, 'alt' ):
                    try:
                        if (img.attrs['alt'] and img.attrs['alt'] != ''):
                            r = self.translate_rating_value(str(img.attrs['alt']))
                            if r != "":
                                break
                    except KeyError:
                        print("KeyError: Skip")
        if r != "":
            return r
        else:
            # print("Something wrong in extracting rating value !")
            return ""

    def translate_rating_value(self, initial_rating_value: str) -> str:
        dictionary = {
            "صحيح": "TRUE", # correct
            "زائف جزئياً": "MIXTURE", # partially-fake
            "عنوان مضلل": "OTHER",  # misleading-title
            "رأي": "OTHER",  # ? (Opinion)
            "ساخر": "OTHER",  # ? (Sarcastique)
            "غير مؤهل": "FALSE",  # ? (Inéligible) not-qualified
            "خادع": "FALSE",  # ? (Trompeur) deceptive
            "زائف": "FALSE", # fake
            "محتوى ناقص": "MIXTURE", # incomplete-title
            "مضلل": "FALSE" # misleading
        }

        tmp_split_str = initial_rating_value.split()
        if  len(tmp_split_str) >= 3:
            for split_str in tmp_split_str:
                if self.translate_rating_value(split_str) !="":
                    initial_rating_value = split_str
                    break     
        
        if initial_rating_value in dictionary:
                return dictionary[initial_rating_value]
        else:
            return ""

    # write this method (and tagme, translate) in an another file cause we can use it in other websites
    @staticmethod
    def get_json_format(tagme_entity):
        '''
            :tagme_entity: must be an object of AnnotateResposte Class returned by tagme function
        '''
        data_set = []
        i = 0
        min_rho = 0.1

        for annotation in tagme_entity.get_annotations(min_rho):
            entity = {}
            entity["id"] = annotation.entity_id
            entity["begin"] = annotation.begin
            entity["end"] = annotation.end
            entity["entity"] = annotation.entity_title
            entity["text"] = annotation.mention
            entity["score"] = annotation.score
            entity["categories"] = []
            if tagme_entity.original_json["annotations"][i]["rho"] > min_rho and "dbpedia_categories" in \
                    tagme_entity.original_json["annotations"][i]:
                for categorie in tagme_entity.original_json["annotations"][i]["dbpedia_categories"]:
                    entity["categories"].append(categorie)
            i = i + 1
            data_set.append(entity)

        return json.dumps(data_set)

    @staticmethod
    def cut_str(str_list):
        # cut string
        result_list = []

        for string in str_list:
            middle = math.floor(len(string) / 2)
            before = string.rindex(' ', 0, middle)
            after = string.index(' ', middle + 1)

            if middle - before < after - middle:
                middle = before
            else:
                middle = after

            result_list.append(string[:middle])
            result_list.append(string[middle + 1:])

        return result_list

    @staticmethod
    def concat_str(str_list):
        result = ""

        for string in str_list:
            result = result + ' ' + string

        return result[1:]

    @staticmethod
    def escape(str):
        str = re.sub('[\n\t\r]', ' ', str)  # removing special char
        str = str.replace('"', '""')  # escaping '"' (CSV format)
        str = re.sub(' {2,}', ' ', str).strip()  # remoing extra spaces
        str = '"' + str + '"'
        return str
