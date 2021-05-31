# -*- coding: utf-8 -*-
import calendar  # convert month name to month number
import json
import re
from typing import *

import requests
from bs4 import BeautifulSoup

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor
from claim_extractor.tagme import tagme


class VishvasnewsFactCheckingSiteExtractor(FactCheckingSiteExtractor):
    TAGME_API_KEY = 'b6fdda4a-48d6-422b-9956-2fce877d9119-843339462'

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def get(self, url):
        """ @return the webpage """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
        html = requests.get(url, headers=headers).text
        soup = BeautifulSoup(html, 'lxml')
        # removing some useless tags
        for s in soup.select("script, iframe, head, header, footer, style"):
            s.decompose()
        return soup

    def post(self, url, data):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}
        html = requests.post(url, data=data, headers=headers).text
        soup = BeautifulSoup(html, 'lxml')
        # removing some useless tags
        for s in soup.select("script, iframe, head, header, footer, style"):
            s.decompose()
        return soup

    def retrieve_listing_page_urls(self) -> List[str]:
        """
            Abstract method. Retrieve the URLs of pages that allow access to a paginated list of claim reviews. This
            concerns some sites where all the claims are not listed from a single point of access but first
            categorized by another criterion (e.g. on politifact there is a separate listing for each possible rating).
            :return: Return a list of listing page urls
        """
        different_urls = []
        different_categories_value = [
            "politics", "society", "world", "viral", "health"]
        url_begins = ["https://www.vishvasnews.com/english/", "https://www.vishvasnews.com/urdu/",
                      "https://www.vishvasnews.com/assamese/", "https://www.vishvasnews.com/tamil/",
                      "https://www.vishvasnews.com/malayalam/"
            , "https://www.vishvasnews.com/gujarati/", "https://www.vishvasnews.com/telugu/",
                      "https://www.vishvasnews.com/marathi/", "https://www.vishvasnews.com/odia/"]
        for url in url_begins:
            for value in different_categories_value:
                different_urls.append(url + value + "/")

        return different_urls

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        """
            A listing page is paginated and will sometimes contain information pertaining to the maximum number of pages
            there are. For sites that do not have that information, please return a negative integer or None
            :param parsed_listing_page:
            :return: The page count if relevant, otherwise None or a negative integer
        """
        return -1

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) -> List[
        str]:
        """
            :parsed_listing_page: --> une page (parsed) qui liste des claims
            :listing_page_url:    --> l'url associé à la page ci-dessus
            :number_of_page:      --> number_of_page
            :return:              --> la liste des url de toutes les claims
        """
        links = []
        select_links = 'ul.listing li div.imagecontent h3 a'
        # links in the static page
        claims = parsed_listing_page.select(
            "div.ajax-data-load " + select_links)
        for link in claims:
            if link["href"]:
                links.append(link["href"])

        # for links loaded by AJAX
        r = re.compile(
            "https://www.vishvasnews.com/(.*)/(.*)[/]").match(listing_page_url)

        lang = r.group(1)
        categorie = r.group(2)

        url_ajax = "https://www.vishvasnews.com/wp-admin/admin-ajax.php"
        data = {
            'action': 'ajax_pagination',
            'query_vars': '{"category_name" : "' + categorie + '", "lang" : "' + lang + '"}',
            'page': 1,
            'loadPage': 'file-archive-posts-part'
        }

        response = self.post(url_ajax, data)

        while True:
            claims = response.select(select_links)
            for link in claims:
                if link['href']:
                    links.append(link['href'])

            if response.find("nav"):
                data['page'] = data['page'] + 1
                response = self.post(url_ajax, data)
                continue
            else:
                break

        return links

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claim = Claim()
        claim_txt = self.extract_claim(parsed_claim_review_page)
        review = self.extract_review(parsed_claim_review_page)
        rating_value = self.extract_rating_value(parsed_claim_review_page)
        claim.set_rating(rating_value)
        claim.set_source("Vishvanews")  # auteur de la review
        claim.review_author = self.extract_author(parsed_claim_review_page)
        claim.set_author(self.extract_claimed_by(
            parsed_claim_review_page))  # ? auteur de la claim?
        # claim.setDatePublished(self.extract_date(parsed_claim_review_page)) #? publication de la claim
        claim.set_claim(claim_txt)
        claim.set_body(review)
        claim.set_refered_links(self.extract_links(parsed_claim_review_page))
        claim.set_title(self.extract_title(parsed_claim_review_page))
        # date de la publication de la review
        claim.set_date(self.extract_date(parsed_claim_review_page))
        claim.set_url(url)
        claim.set_tags(self.extract_tags(parsed_claim_review_page))

        # extract_entities returns two variables
        json_claim, json_body = self.extract_entities(claim_txt, review)
        claim.claim_entities = json_claim
        claim.body_entities = json_body
        return [claim]

    def is_claim(self, parsed_claim_review_page: BeautifulSoup) -> bool:
        rating_value = parsed_claim_review_page.select_one(
            "div.selected span")
        return bool(rating_value)

    def extract_claim(self, parsed_claim_review_page: BeautifulSoup) -> str:
        claim = parsed_claim_review_page.select_one("ul.claim-review li span")
        # check that the claim is in english
        if claim:
            return self.escape(claim.text)
        else:
            return ""

    def extract_title(self, parsed_claim_review_page: BeautifulSoup) -> str:
        title = parsed_claim_review_page.find("h1", class_="article-heading")
        if title:
            return self.escape(title.text)
        else:
            return ""

    def extract_review(self, parsed_claim_review_page: BeautifulSoup) -> str:
        review = ""
        paragraphs = parsed_claim_review_page.select("div.lhs-area > p")

        if paragraphs:
            for paragraph in paragraphs:
                review += paragraph.text + " "

        return self.escape(review)

    def extract_claimed_by(self, parsed_claim_review_page: BeautifulSoup) -> str:
        review = parsed_claim_review_page.select("ul.claim-review li span")

        if len(review) > 1:
            return self.escape(review[1].text)
        else:
            return ""

    def extract_links(self, parsed_claim_review_page: BeautifulSoup) -> str:
        links = []

        # extracting the main article body
        review_body = parsed_claim_review_page.select_one(
            "div.lhs-area")

        # extracting links
        for paragraph_tag in review_body.find_all("p"):
            for link_tag in paragraph_tag.find_all("a"):
                if link_tag.has_attr('href'):
                    links.append(link_tag['href'])

        # Links to embedded tweets
        for figure_tag in review_body.find_all("figure"):
            iframe = figure_tag.find("iframe")
            if iframe is not None:
                if iframe.has_attr('src'):
                    links.append(iframe['src'])
                elif iframe.has_attr("data-src"):
                    links.append(iframe['data-src'])

        return self.escape(str(links))

    def extract_date(self, parsed_claim_review_page: BeautifulSoup) -> str:
        date = parsed_claim_review_page.select("ul.updated li")[1].text.strip()
        if not date:
            return ""

        r = re.compile(
            '^Updated: *([a-zA-Z]+) ([0-9]+), ([0-9]{4})$').match(date)

        month = str({v: k for k, v in enumerate(
            calendar.month_name)}[r.group(1)])
        day = r.group(2)
        year = r.group(3)

        date = year + '-' + month + '-' + day
        return date

    def extract_tags(self, parsed_claim_review_page: BeautifulSoup) -> str:
        """
            : parsed_claim_review_page: - -> the parsed web page of the claim
            : return: - -> return a list of tags that are related to the claim
        """
        tags_link = parsed_claim_review_page.select(
            "ul.tags a")
        tags = []
        for tag_link in tags_link:
            if tag_link.text:
                tags.append((tag_link.text).replace("#", ""))

        return self.escape(str(tags))

    def extract_author(self, parsed_claim_review_page: BeautifulSoup) -> str:
        authors = []

        for author in parsed_claim_review_page.select("li.name a"):
            authors.append(author.text)

        return ",".join(authors)

    def extract_rating_value(self, parsed_claim_review_page: BeautifulSoup) -> str:
        btn = parsed_claim_review_page.select_one(
            "div.selected span")
        if btn:
            return btn.text.strip()
        else:
            return ""

    def extract_entities(self, claim: str, review: str):
        """
            You should call extract_claim and extract_review method and
            store the result in self.claim and self.review before calling this method
            :return: --> claim_entities in the claim and the review in to different variable
        """
        return self.escape(self.get_json_format(self.tagme(claim))), self.escape(
            self.get_json_format(self.tagme(review)))

    @staticmethod
    def translate_rating_value(initial_rating_value: str) -> str:
        return initial_rating_value

    @staticmethod
    def tagme(text) -> list:
        """
            :text:  --> The text in english after translation
            :return:  --> return a list of claim_entities
        """
        #if text == "":
        #    return []
        #tagme.GCUBE_TOKEN = VishvasnewsFactCheckingSiteExtractor.TAGME_API_KEY
        #return tagme.annotate(text)
        return []


    # write this method (and tagme, translate) in an another file cause we can use it in other websites
    @staticmethod
    def get_json_format(tagme_entity):
        '''
            :tagme_entity: must be an object of AnnotateResponse Class returned by tagme function
        '''
        data_set = []
        i = 0
        min_rho = 0.1

        # in case tagme() method return nothing
        if tagme_entity != []:
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
    def escape(str):
        str = re.sub('[\n\t\r]', ' ', str)  # removing special char
        str = str.replace('"', '""')  # escaping '"' (CSV format)
        str = re.sub(' {2,}', ' ', str).strip()  # remoing extra spaces
        str = '"' + str + '"'
        return str
