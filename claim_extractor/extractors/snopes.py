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
        next_link = parsed_listing_page.find("a", {"class", "btn-next btn"})['href']
        next_page_contents = caching.get(next_link, headers=self.headers, timeout=5)
        next_page = BeautifulSoup(next_page_contents, "lxml")

        title_text = next_page.find(
            "title").text  # Format u'Fact Checks Archive | Page 2 of 1069 | Snopes.com'
        max_page_pattern = re.compile("Page [0-9]+ of ([0-9+]+)")
        result = max_page_pattern.match(title_text.split("|")[1].strip())
        max_page = int(result.group(1))
        return max_page

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = self.extract_urls(parsed_listing_page)
        for page_number in tqdm(range(2, number_of_pages)):
            if 0 < self.configuration.maxClaims < len(urls):
                break
            url = listing_page_url + "/page/" + str(page_number)
            page = caching.get(url, headers=self.headers, timeout=5)
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls = urls + self.extract_urls(current_parsed_listing_page)
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = list()
        links = parsed_listing_page.findAll("article", {"class": "media-wrapper"})
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
        claim.set_url(url)
        claim.set_source("snopes")

        # title
        article = parsed_claim_review_page.find("article", {'class', 'main-post'})
        header = article.find("header")
        title = header.find("h1")
        claim.set_title(title.text)

        card = article.find("div", {"class": "content-wrapper card"})
        card_body = card.find("div", {'class': 'content'})

        # date
        date_str = ""
        rating = None
        claim_text = None
        date_ = parsed_claim_review_page.find('span', {"class": "date date-published"})
        # print date_["content"]
        if not date_:
            date_ = parsed_claim_review_page.find('span', {"class": "date date-last-update"})
        if date_:
            date_str = dateparser.parse(date_.text).strftime("%Y-%m-%d")

        # body

        ads = card_body.findAll("div")
        for ad in ads:
            ad.decompose()

        ads = card_body.findAll("div", {"class": "snopes-bt"})
        for ad in ads:
            ad.decompose()

        text = ""
        contents = card_body.findChildren()
        for child in contents:
            text += child.text

        body_description = text

        # author
        author = parsed_claim_review_page.find("a", {"class": "author"})

        rating_div = None
        if not rating:
            rating = parsed_claim_review_page.find("span", {"class": "rating-name"})
        if not rating:
            rating_div = parsed_claim_review_page.find("div", {"class": "media rating"})
        if not rating and not rating_div:
            rating_div = parsed_claim_review_page.find("div", {"class": "claim-old"})
        if not rating and not rating_div:
            rating_div = parsed_claim_review_page.find("div", {"class": "rating-wrapper card"})
        if rating_div:
            rating = rating_div.find("h5")
            if not rating:
                rating = rating_div.find("span")
        if not rating:
            # Oldest page format
            rating = parsed_claim_review_page.find("font", {"class", "status_color"})
            if rating:
                rating = rating.find("b")

        # related links
        related_links = []
        for link in card_body.findAll('a', href=True):
            related_links.append(link['href'])

        if not claim_text:
            claim_p = parsed_claim_review_page.find('p', {"class": "claim"})
            if not claim_p:
                claim_div = parsed_claim_review_page.find('div', {"class": "claim"})
                if not claim_div:
                    claim_div = parsed_claim_review_page.find('div', {"class": "claim-old"})
                if not claim_div:
                    claim_text = ""
                else:
                    claim_text = claim_div.find("p").text

            else:
                claim_text = claim_p.text
        else:
            claim_text = claim_text.strip()

        tags = []
        for tag in parsed_claim_review_page.findAll('meta', {"property": "article:tag"}):
            tags.append(tag["content"])

        if not date_str or not claim_text or not body_description or not rating:
            claim_text, body_description, date_str, rating = handle_legacy_page_structures(card_body, claim_text,
                                                                                           body_description,
                                                                                           date_str, rating)
        claim.set_date(date_str)
        claim.set_body(body_description)
        claim.set_tags(", ".join(tags))
        claim.set_refered_links(related_links)

        if author:
            claim.review_author = author.text.strip()

        if len(claim_text) > 3 and len(claim_text.split("\n")) < 5:
            claim.set_claim(claim_text)
        else:
            if header:
                h1 = header.find("h1")
                claim_text = h1.text
                if claim_text:
                    claim.set_claim(claim_text)
                else:
                    print("Claim text cannot be found!")
                    return []


            else:
                return []

        if rating:
            claim.set_alternate_name(rating.text)
        else:
            return []

        return [claim]


def handle_legacy_page_structures(card_body, claim_text, body_description, date_str, rating):
    # Happens sometimes that the rating is embedded deep into a table...
    rating_table = card_body.findAll("table")
    if rating_table and len(rating_table) > 0:
        tds = rating_table[0].findAll("td")
        if len(tds) > 1:
            status = tds[1].find("font")
            if status:
                b = status.find("b")
                if b:
                    status = b
                strong = status.find("strong")
                if strong:
                    status = strong
                rating = status

    tbody = card_body.find("tbody")
    if tbody:
        card_body = tbody

    paras = card_body.findAll("p")
    in_origin = False
    previous_was_claim = False
    para_index = -1
    for para in paras:
        para_index += 1
        font = para.find("font")
        if not font:
            font = para.find("span")
        if font:
            font_b = font.find("b")
            if font_b:
                font = font_b

        if not previous_was_claim:
            if font and "This article has been moved" in font.text:
                rating = None
            if font and "Topic:" in font.text:
                rating = None
            if font and ("FACT CHECK" in font.text):
                font.decompose()
                in_origin = False
                if claim_text is None or len(claim_text) == 0:
                    claim_text = para.text.strip()
            elif font and ("Claim" in font.text):
                previous_was_claim = True
                font.decompose()
                in_origin = False
                if claim_text is None or len(claim_text) == 0:
                    claim_text = para.text.strip()
            elif font and ("Virus" in font.text):
                font.decompose()
                in_origin = False
                if claim_text is None or len(claim_text) == 0:
                    claim_text = para.text.strip()
                rating = DummyTag()
                rating.text = "Virus"
            elif font and ("Joke" in font.text):
                font.decompose()
                in_origin = False
                if claim_text is None or len(claim_text) == 0:
                    claim_text = para.text.strip()
                rating = DummyTag()
                rating.text = "Joke"
            elif font and ("Glurge" in font.text):
                font.decompose()
                in_origin = False
                if claim_text is None or len(claim_text) == 0:
                    claim_text = para.text.strip()
                rating = DummyTag()
                rating.text = "Glurge"
            elif font and ("Scam:" in font.text):
                font.decompose()
                in_origin = False
                if claim_text is None or len(claim_text) == 0:
                    claim_text = para.text.strip()
                rating = DummyTag()
                rating.text = "Scam"
            elif font and ("Phishing bait" in font.text or "Phish Bait" in font.text):
                font.decompose()
                in_origin = False
                if claim_text is None or len(claim_text) == 0:
                    claim_text = para.text.strip()
                rating = DummyTag()
                rating.text = "Phishing bait"
            elif font and ("Virus name" in font.text):
                font.decompose()
                in_origin = False
                if claim_text is None or len(claim_text) == 0:
                    claim_text = para.text.strip()
                rating = DummyTag()
                rating.text = "Virus"
            elif font and ("Legend" in font.text):
                font.decompose()
                in_origin = False
                if claim_text is None or len(claim_text) == 0:
                    claim_text = para.text.strip()
                rating = DummyTag()
                rating.text = "Legend"
            elif font and ("Rumor" in font.text):
                font.decompose()
                in_origin = False
                if claim_text is None or len(claim_text) == 0:
                    claim_text = para.text.strip()
                rating = DummyTag()
                rating.text = "Rumor"
        elif previous_was_claim:
            previous_was_claim = False
            noindex = para.find("noindex")
            if noindex:
                para = noindex

            fonts = para.findAll("font")
            title_font_tag = None
            span = None
            if len(fonts) > 0:
                title_font_tag = fonts[0]
            if title_font_tag:
                b_in_title = title_font_tag.find("b")
                if b_in_title:
                    title_font_tag = b_in_title

                if "Status:" in title_font_tag.text:
                    b = fonts[1].find("b")
                    if b:
                        rating = b.find("i")
                    else:
                        rating = fonts[1]
            else:
                span = para.find("span")
                if span:
                    span = span.find("span")
                if span and "Example" not in span.text:
                    b = span.find("b")
                    if b:
                        span = b
                    rating = span

        if font and ("Origin:" in font.text or "Origins:" in font.text):
            font.decompose()
            in_origin = True
            body_description += para.text
        if font and ("Last updated:" in font.text):
            in_origin = False
            font.decompose()
            parsed_date = dateparser.parse(para.text.strip())
            if parsed_date:
                date_str = parsed_date.strftime("%Y-%m-%d")

        if in_origin:
            body_description += para.text

    return claim_text, body_description, date_str, rating
