# -*- coding: utf-8 -*-
import re
from typing import List, Set

from bs4 import BeautifulSoup
from dateparser.search import search_dates
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


class FactscanFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def retrieve_listing_page_urls(self) -> List[str]:
        return ["http://factscan.ca/page/1"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        page_nav = parsed_listing_page.find("div", {"class": "pagenav clearfix"})
        last_page_link = page_nav.findAll("a")[-1]['href']
        page_re = re.compile("http://factscan.ca/page/([0-9]+)/")
        max_page = int(page_re.match(last_page_link).group(1))
        return max_page

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = self.extract_urls(parsed_listing_page)
        for page_number in tqdm(range(2, number_of_pages)):
            url = "http://factscan.ca/page/" + str(page_number) + "/"
            page = caching.get(url, headers=self.headers, timeout=5)
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls +=self.extract_urls(current_parsed_listing_page)
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = list()
        links = parsed_listing_page.findAll("h1", {"class": "post-title entry-title home-feed-title"})
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
        claim = Claim()
        claim.set_url(url)
        claim.set_source("factscan")

        json_ = None
        if parsed_claim_review_page.find("script", {"type": "application/ld+json"}):
            json_ = parsed_claim_review_page.find("script", {"type": "application/ld+json"}).get_text()

        def parse_wrong_json(json_, left, right):
            if json_:
                if len(json_.split(left)) > 0:
                    return json_.split(left)[1].split(right)[0]
            else:
                return None

            # Summary box

        summary_box = parsed_claim_review_page.find("div", {"class": "summary-box"})

        # title
        title = parsed_claim_review_page.find("meta", {"property": "og:title"})['content']
        claim.set_title(title)

        # claim review date
        date = parsed_claim_review_page.find('meta', {"property": "article:published_time"})
        if date:
            date_str = search_dates(date['content'].split("T")[0])[0][1].strftime("%Y-%m-%d")
            claim.set_date(date_str)

        # Creative work date

        summary_text = summary_box.find("p").text
        date_published = ""
        if " on " in summary_text:
            date_published = summary_text.split(" on ")[-1].strip()
        else:
            if " published " in summary_text:
                date_published = summary_text.split(" published ")[-1].strip()
            elif " dated " in summary_text:
                date_published = summary_text.split(" dated ")[-1].strip()
            elif " from " in summary_text:
                date_published = summary_text.split(" from ")[-1].strip()
            elif " sent " in summary_text:
                date_published = summary_text.split(" in ")[-1].strip()
            elif " in " in summary_text:
                date_published = summary_text.split(" in ")[-1].strip()

        if len(date_published) > 0:
            date_published = search_dates(date_published)[0][1].strftime("%Y-%m-%d")
            claim.setDatePublished(date_published)

        # rating
        if json_:
            claim.set_rating_value(parse_wrong_json(json_, '"ratingValue":', ","))
            claim.setWorstRating(parse_wrong_json(json_, '"worstRating":', ","))
            claim.set_best_rating(parse_wrong_json(json_, '"bestRating":', ","))
            claim.set_alternate_name(parse_wrong_json(json_, '"alternateName":', ","))
        # when there is no json
        else:
            if parsed_claim_review_page.find("div", {"class": "fact-check-icon"}):
                if parsed_claim_review_page.find("div", {"class": "fact-check-icon"}).find('img'):
                    claim_str = \
                        parsed_claim_review_page.find("div", {"class": "fact-check-icon"}).find('img')['alt'].split(
                            ":")[1]
                    claim.alternate_name = claim_str.strip()

        # body
        body = parsed_claim_review_page.find("div", {"class": "entry-content"})
        claim.set_body(body.get_text())

        # author
        author = parsed_claim_review_page.find("div", {"class": "sharethefacts-speaker-name"})
        if not author:
            author = summary_box.find("p").find("strong")

        if author:
            claim.set_author(author.text)

        # same_as
        claim.setSameAs(parse_wrong_json(json_, '"sameAs": [', "]"))

        # related links
        divTag = parsed_claim_review_page.find("div", {"class": "entry-content"})
        related_links = []
        for link in divTag.findAll('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        if parsed_claim_review_page.find("div", {"class": "sharethefacts-statement"}):
            claim.set_claim(parsed_claim_review_page.find("div", {"class": "sharethefacts-statement"}).get_text())
        else:
            claim.set_claim(claim.title)

        tags = []

        for tag in parsed_claim_review_page.findAll('meta', {"property": "article:tag"}):
            tags.append(tag["content"])
        if len(tags) == 0:
            for tag in parsed_claim_review_page.findAll("a", {"rel": "category tag"}):
                tags.append(tag.text)
        claim.set_tags(", ".join(tags))

        return [claim]
