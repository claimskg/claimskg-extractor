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
        return ['https://www.politifact.com/factchecks/'] #changes
    
    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        max_page = 1000
        return max_page
    
    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = self.extract_urls(parsed_listing_page)
        #print(urls)
        page_number = 2
        while True : ###changes
            url = listing_page_url + "?page=" + str(page_number)
            #print(url)
            page = caching.get(url, headers=self.headers, timeout=5)
            if page is not None:
                current_parsed_listing_page = BeautifulSoup(page, "lxml")
            else:
                break

            nav_buttons = current_parsed_listing_page.find_all("section", attrs={'class': 't-row'})
            nav_buttons = nav_buttons[-1].find_all("li", attrs={'class': 'm-list__item'})

            if len(nav_buttons) == 1:
                break
            else:
                urls += self.extract_urls(current_parsed_listing_page)
            page_number += 1
            #print("\rr: " + url)
        print(urls)    
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
        #print("\r" + url)

        claim.set_source("politifact")

        # Claim
        title = parsed_claim_review_page.find("div", {"class": "m-statement__quote"})
        claim.set_claim(title.text.strip())

        # title
        title = parsed_claim_review_page.find("h2", {"class": "c-title"})
        claim.set_title(title.text.strip())
        
        # date
        date = parsed_claim_review_page.find('span', {"class": "m-author__date"})
        if date:
            date_str = search_dates(date.text)[0][1].strftime("%Y-%m-%d")
            claim.set_date(date_str)

        # rating
        # https://static.politifact.com/politifact/rulings/meter-mostly-false.jpg
        statement_body=parsed_claim_review_page.find("div", {"class", "m-statement__body"})
        statement_detail = statement_body.find("div", {"class", "c-image"})
        statement_detail_image=statement_detail.find("picture")
        statement_detail_image_alt=statement_detail_image.find("img",{"class", "c-image__original"})
        if statement_detail_image_alt:
            #claim.alternate_name = statement_detail_image_alt['src'].split("rulings/")[1].split(".jpg")[0]            
            if self.translate_rating_value(statement_detail_image_alt['alt']) != "":
                claim.rating = self.translate_rating_value(statement_detail_image_alt['alt'])
            else:
                claim.rating = statement_detail_image_alt['alt']

        # body
        body = parsed_claim_review_page.find("article", {"class": "m-textblock"})
        #body.find("div", {"class": "artembed"}).decompose()
        #claim.set_body(body.get_text())

        

        
        
        text =""
        if parsed_claim_review_page.select( 'main > section > div.t-row__center > article.m-textblock' ):
            for child in parsed_claim_review_page.select( 'main > section > div.t-row__center > article.m-textblock' ):
                for element in child.contents:
                    if (element.name == "div"):
                        valid = True
                        # check for illegal JS element in artembed (tag):
                        if (hasattr( element, 'class' )):
                            try:
                                if ('class' in element.attrs):
                                    if (element.attrs['class'][0] == "artembed"):
                                        if (element.text.startswith("\r\nwindow.gciAnalyticsUAID")):
                                            valid = False
                            except KeyError:
                                print("KeyError: Skip")
                    else:
                        valid = True
                        if hasattr( element, 'text' ):
                            #if (element.text == "We rate this claim False." and url == "https://www.politifact.com/staff/kelsey-tamakloe/"):
                            if (url == "https://www.politifact.com/staff/kelsey-tamakloe/"):
                                print("\r" + str(element.text))
                    if (valid == True):
                        if (element):
                            if (hasattr( element, 'text' )):
                                text += " " + str(element.text)
                            else:
                                text += " " + str(element)

            body_description = text.strip()
            claim.body = str(body_description).strip()

        # author
        author_meta = parsed_claim_review_page.find("div", {"class": "m-author__content"})
        if author_meta:
            author = author_meta.find("a").text
            claim.set_author(author)
            author_url = author_meta.find("a")
            if author_url.attrs["href"] != "":
                claim.author_url = "https://www.politifact.com" + author_url.attrs["href"]

        # date published
        statement_meta = parsed_claim_review_page.find("div", {"class": "m-statement__meta"})
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
                    claim.date = date
        
        # related links
        div_tag = parsed_claim_review_page.find("article", {"class": "m-textblock"})
        related_links = []
        for link in body.find_all('a', href=True):
            try:
                if (link['href'][0] == "/"):
                        related_links.append("https://www.politifact.com" + link['href']) ##########changes
                else:
                    related_links.append(link['href'])
                claim.set_refered_links(related_links)
            except KeyError as e:
                    print("->KeyError: " + str(e))
                    continue
            except IndexError as e:
                    print("->IndexError: " + str(e))
                    continue

        claim.set_claim(parsed_claim_review_page.find("div", {"class": "m-statement__quote"}).text.strip())
        
        tags = []
        ul_tag = parsed_claim_review_page.find("ul", {"class", "m-list"})
        if ul_tag:
            ul_tag_contents = ul_tag.findAll("li", {"class", "m-list__item"})
            for a in ul_tag_contents:
                a_tag=a.find("a", title=True)
                a_tag_text=a_tag['title']
                tags.append(a_tag_text)

        if statement_body:
            topics = statement_body.find("ul", {"class", "m-list"}).find_all("a")
            for link in topics:
                text = link['title']
                tags.append(text)
            claim.set_tags(",".join(tags))

        return [claim]

    def translate_rating_value(self, initial_rating_value: str) -> str:
        dictionary = {
            "true": "True",
            "mostly-true": "Mostly True",
            "half-true": "Half False",
            "barely-true": "Mostly False",
            "false": "False",
            "pants-fire": "Pants on Fire"
        }
    
        if initial_rating_value in dictionary:
                return dictionary[initial_rating_value]
        else:
            return ""
