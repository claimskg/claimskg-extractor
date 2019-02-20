# -*- coding: utf-8 -*-
import re
from typing import List, Set, Optional

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
        next_link = parsed_listing_page.find("a", {"class", "btn-next btn btn-outline-primary"})['href']
        next_page_contents = caching.get(next_link, headers=self.headers, timeout=5)
        next_page = BeautifulSoup(next_page_contents, "lxml")

        title_text = next_page.find(
            "title").text  # Format u'Fact Checks Archive | Page 2 of 1069 | Snopes.com'
        max_page_pattern = re.compile("Page [0-9]+ of ([0-9+]+)")
        result = max_page_pattern.match(title_text.split("|")[1].strip())
        max_page = int(result.group(1))
        return max_page

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> Set[str]:
        urls = self.extract_urls(parsed_listing_page)
        for page_number in tqdm(range(2, number_of_pages)):
            if 0 < self.configuration.maxClaims < len(urls):
                break
            url = listing_page_url + "/page/" + str(page_number)
            page = caching.get(url, headers=self.headers, timeout=5)
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls = set.union(urls, self.extract_urls(current_parsed_listing_page))
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = set()
        links = parsed_listing_page.findAll("article", {"class": "list-group-item media"})
        for anchor in links:
            anchor = anchor.find('a', {"class": "link"}, href=True)
            url = str(anchor['href'])
            max_claims = self.configuration.maxClaims
            if 0 < max_claims <= len(urls):
                break
            if url not in self.configuration.avoid_urls:
                urls.add(url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> Optional[Claim]:
        if url in url_blacklist:
            return None

        claim = Claim()
        claim.setUrl(url)
        claim.setSource("snopes")

        # title
        title = parsed_claim_review_page.find("h1", {"class": "card-title"})
        claim.setTitle(title.text)

        # date
        date_str = ""
        body_description = ""
        rating = None
        claim_text = None
        date_ = parsed_claim_review_page.find('span', {"class": "date-published"})
        # print date_["content"]
        if date_:
            date_str = dateparser.parse(date_.text).strftime("%Y-%m-%d")
        else:  # post-body-card
            card_body = parsed_claim_review_page.find("main").find("article").find("div",
                                                                                   {"class": "post-body-card"}).find(
                "div", {"class": "card-body"})

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

            paras = card_body.findAll("p")
            in_origin = False
            for para in paras:
                font = para.find("font")
                if not font:
                    font = para.find("span")
                if font:
                    font_b = font.find("b")
                    if font_b:
                        font = font_b
                if font and "This article has been moved" in font.text:
                    return None
                if font and "Topic:" in font.text:
                    return None
                if font and ("FACT CHECK" in font.text):
                    font.decompose()
                    in_origin = False
                    claim_text = para.text.strip()
                elif font and ("Claim:" in font.text or "Virus" in font.text or "Joke" in font.text):
                    font.decompose()
                    in_origin = False
                    claim_text = para.text.strip()
                elif font and ("Glurge:" in font.text):
                    font.decompose()
                    in_origin = False
                    claim_text = para.text.strip()
                    rating = DummyTag()
                    rating.text = "Glurge"
                elif font and ("Scam:" in font.text):
                    font.decompose()
                    in_origin = False
                    claim_text = para.text.strip()
                    rating = DummyTag()
                    rating.text = "Scam"
                elif font and ("Legend:" in font.text):
                    font.decompose()
                    in_origin = False
                    claim_text = para.text.strip()
                    rating = DummyTag()
                    rating.text = "Legend"
                noindex = para.find("noindex")
                if noindex:
                    fonts = noindex.findAll("font")
                    title_font_tag = None
                    span = None
                    if len(fonts) > 0:
                        title_font_tag = fonts[0]
                    elif title_font_tag:
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
                        span = noindex.find("span")
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
        claim.setDate(date_str)
        claim.setDatePublished(date_str)

        # body
        body = parsed_claim_review_page.find("div", {"class": "post-body-card"})
        card = body.find("div", {"class": "card-body"})
        ads = card.findAll("div", {"class": "creative"})
        for ad in ads:
            ad.decompose()

        ads = card.findAll("div", {"class": "snopes-bt"})
        for ad in ads:
            ad.decompose()

        text = ""
        contents = card.findChildren()
        for child in contents:
            text += child.text

        body_description = body.get_text()

        claim.setBody(body_description)

        # author
        author = parsed_claim_review_page.find("a", {"class": "author"})
        if author:
            claim.setAuthor(author.text)

        if not rating:
            rating = parsed_claim_review_page.find("span", {"class": "rating-name"})

        if not rating:
            # Oldest page format
            rating = parsed_claim_review_page.find("font", {"class", "status_color"})
            if rating:
                rating = rating.find("b")

        if rating:
            claim.alternate_name = rating.text
        else:
            return None
        # related links
        div_tag = parsed_claim_review_page.find("div", {"class": "post-body-card"})
        related_links = []
        for link in div_tag.findAll('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        if not claim_text:
            claim_p = parsed_claim_review_page.find('p', {"class": "claim"})
            if not claim_p:
                claim_text = div_tag.text

            else:
                claim_text = claim_p.text

        claim.setClaim(claim_text)

        tags = []

        for tag in parsed_claim_review_page.findAll('meta', {"property": "article:tag"}):
            tags.append(tag["content"])
        claim.set_tags(", ".join(tags))

        return claim
