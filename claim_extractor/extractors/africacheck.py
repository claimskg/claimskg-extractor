# -*- coding: utf-8 -*-
import re
from typing import List

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag, NavigableString
from dateparser.search import search_dates
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


def get_all_claims(criteria):
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

    # performing a search by each letter, and adding each article to a urls_ var.
    urls_ = {}
    last_page = []
    for page_number in range(1, 500):
        if 0 < criteria.maxClaims <= len(urls_):
            break

        url = "https://africacheck.org/latest-reports/page/" + str(page_number) + "/"
        try:
            page = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(page.text, "lxml")
            soup.prettify()
            links = soup.findAll("div", {"class": "article-content"})
            if (len(links) != 0) or (links != last_page):
                for anchor in links:
                    anchor = anchor.find('a', href=True)
                    ind_ = str(anchor['href'])
                    if ind_ not in list(urls_.keys()):
                        if 0 < criteria.maxClaims <= len(urls_):
                            break
                        if ind_ not in criteria.avoid_url:
                            urls_[ind_] = ind_
                            print("adding " + str(ind_))
                last_page = links
            else:
                print("break!")
                break
        except:
            print("error=>" + str(url))

    claims = []
    index = 0
    # visiting each article's dictionary and extract the content.
    for url, conclusion in urls_.items():
        print(str(index) + "/" + str(len(list(urls_.keys()))) + " extracting " + str(url))
        index += 1

        url_complete = str(url)

        # print url_complete
        # try:
        page = requests.get(url_complete, headers=headers, timeout=5)
        soup = BeautifulSoup(page.text, "lxml")
        soup.prettify("utf-8")

        claim_ = Claim()
        claim_.set_url(url_complete)
        claim_.set_source("africacheck")

        # title
        title = soup.find("meta", {"property": "og:title"})
        title_content = title['content']
        if "|" in title_content:
            title_content = title_content.split("|")[-1]
        claim_.set_title(title_content)

        # date

        date_ = soup.find('time')
        # print date_["content"]
        if date_:
            date_str = search_dates(date_['datetime'].split(" ")[0])[0][1].strftime("%Y-%m-%d")
            # print date_str
            claim_.set_date(date_str)
        # print claim_.date

        # rating

        truth_rating = ""
        if soup.find("div", {"class": "verdict-stamp"}):
            truth_rating = soup.find("div", {"class": "verdict-stamp"}).get_text()
        if soup.find("div", {"class": "verdict"}):
            truth_rating = soup.find("div", {"class": "verdict"}).get_text()
        if soup.find("div", {"class": "indicator"}):
            truth_rating = soup.find("div", {"class": "indicator"}).get_text()
            if soup.find("div", {"class": "indicator"}).find('span'):
                truth_rating = soup.find("div", {"class": "indicator"}).find('span').get_text()

        claim_.set_alternate_name(str(re.sub('[^A-Za-z0-9 -]+', '', truth_rating)).lower().strip())

        # when there is no json

        date_ = soup.find("time", {"class": "datetime"})
        if date_:
            claim_.set_date(date_.get_text())

        # body
        body = soup.find("div", {"id": "main"})
        claim_.set_body(body.get_text())

        # author
        author = soup.find("div", {"class": "sharethefacts-speaker-name"})
        if author:
            claim_.set_author(author.get_text())

        # related links
        divTag = soup.find("div", {"id": "main"})
        related_links = []
        for link in divTag.findAll('a', href=True):
            related_links.append(link['href'])
        claim_.set_refered_links(related_links)

        if soup.find("div", {"class": "report-claim"}):
            claim_.set_claim(soup.find("div", {"class": "report-claim"}).find("strong").get_text())
        else:
            claim_.set_claim(claim_.title)

        tags = []

        for tag in soup.findAll('meta', {"property": "article:tag"}):
            tags.append(tag["content"])
        claim_.set_tags(", ".join(tags))

        claims.append(claim_.generate_dictionary())

    # creating a pandas dataframe
    pdf = pd.DataFrame(claims)
    return pdf


class AfricacheckFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def retrieve_listing_page_urls(self) -> List[str]:
        return ["https://africacheck.org/latest-reports/page/1/"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        last_page_link = parsed_listing_page.findAll("a", {"class": "page-numbers"})[-2]['href']
        page_re = re.compile("https://africacheck.org/latest-reports/page/([0-9]+)/")
        max_page = int(page_re.match(last_page_link).group(1))
        return max_page

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = self.extract_urls(parsed_listing_page)
        for page_number in tqdm(range(2, number_of_pages)):
            url = "https://africacheck.org/latest-reports/page/" + str(page_number) + "/"
            page = caching.get(url, headers=self.headers, timeout=5)
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls += self.extract_urls(current_parsed_listing_page)
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = list()
        links = parsed_listing_page.findAll("div", {"class": "article-content"})
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
        local_claims = []
        claim = Claim()
        claim.set_url(url)
        claim.set_source("africacheck")

        # title
        title = parsed_claim_review_page.find("meta", {"property": "og:title"})
        global_title_text = title['content']
        claim.set_title(global_title_text)

        # date
        date = parsed_claim_review_page.find('time')
        global_date_str = ""
        if date:
            global_date_str = search_dates(date['datetime'].split(" ")[0])[0][1].strftime("%Y-%m-%d")
            claim.set_date(global_date_str)

        # rating
        global_truth_rating = ""
        if parsed_claim_review_page.find("div", {"class": "verdict-stamp"}):
            global_truth_rating = parsed_claim_review_page.find("div", {"class": "verdict-stamp"}).get_text()
        if parsed_claim_review_page.find("div", {"class": "verdict"}):
            global_truth_rating = parsed_claim_review_page.find("div", {"class": "verdict"}).get_text()
        if parsed_claim_review_page.find("div", {"class": "indicator"}):
            global_truth_rating = parsed_claim_review_page.find("div", {"class": "indicator"}).get_text()
            if parsed_claim_review_page.find("div", {"class": "indicator"}).find('span'):
                global_truth_rating = parsed_claim_review_page.find("div", {"class": "indicator"}).find(
                    'span').get_text()

        claim.set_alternate_name(str(re.sub('[^A-Za-z0-9 -]+', '', global_truth_rating)).lower().strip())

        # author
        author = parsed_claim_review_page.find("div", {"class": "sharethefacts-speaker-name"})
        if author:
            claim.set_author(author.get_text())

        # when there is no json

        date = parsed_claim_review_page.find("time", {"class": "datetime"})
        if date:
            claim.set_date(date.get_text())

        tags = []

        for tag in parsed_claim_review_page.findAll('meta', {"property": "article:tag"}):
            tags.append(tag["content"])
        claim.set_tags(", ".join(tags))

        global_claim_text = ""
        report_claim_div = parsed_claim_review_page.find("div", {"class": "report-claim"})
        if report_claim_div:
            claim.set_claim(report_claim_div.find("p").get_text())
        else:
            claim.set_claim(claim.title)

        inline_ratings = parsed_claim_review_page.findAll("div", {"class", "inline-rating"})
        entry_section = parsed_claim_review_page.find("section", {"class", "entry-content"})  # type: Tag
        entry_section_full_text = entry_section.text

        # There are several claims checked within the page. Common date, author, tags ,etc.
        if inline_ratings and len(inline_ratings) > 0:
            entry_contents = entry_section.contents  # type : List[Tag]
            current_index = 0

            # First we extract the bit of text common to everything until we meed a sub-section
            body_text, links, current_index = get_text_and_links_until_next_header(entry_contents, current_index)
            claim.set_body(body_text)
            claim.set_refered_links(links)

            while current_index < len(entry_contents):
                current_index = forward_until_inline_rating(entry_contents, current_index)
                inline_rating_div = entry_contents[current_index]
                if isinstance(inline_rating_div, NavigableString):
                    break
                claim_text = inline_rating_div.find("p", {"class": "claim-content"}).text
                inline_rating = inline_rating_div.find("div", {"class", "indicator"}).find("span").text
                previous_current_index = current_index
                inline_body_text, inline_links, current_index = get_text_and_links_until_next_header(entry_contents,
                                                                                                     current_index)
                if previous_current_index == current_index:
                    current_index += 1
                inline_claim = Claim()
                inline_claim.set_source("africacheck")
                inline_claim.set_claim(claim_text)
                inline_claim.set_alternate_name(inline_rating)
                inline_claim.set_refered_links(",".join(inline_links))
                inline_claim.set_body(inline_body_text)
                inline_claim.set_tags(", ".join(tags))
                inline_claim.set_date(global_date_str)
                inline_claim.set_url(url)
                if author:
                    inline_claim.set_author(author.get_text())
                inline_claim.set_title(global_title_text)

                local_claims.append(inline_claim)
        elif "PROMISE:" in entry_section_full_text and "VERDICT:" in entry_section_full_text:
            entry_contents = entry_section.contents  # type : List[Tag]
            current_index = 0

            # First we extract the bit of text common to everything until we meed a sub-section
            body_text, links, current_index = get_text_and_links_until_next_header(entry_contents, current_index)
            claim.set_body(body_text)
            claim.set_refered_links(links)

            while current_index < len(entry_contents):
                inline_rating_div = entry_contents[current_index]
                if isinstance(inline_rating_div, NavigableString):
                    break
                claim_text = entry_contents[current_index + 2].span.text
                inline_rating = entry_contents[current_index + 4].span.text
                current_index += 5
                previous_current_index = current_index
                inline_body_text, inline_links, current_index = get_text_and_links_until_next_header(entry_contents,
                                                                                                     current_index)
                if previous_current_index == current_index:
                    current_index += 1
                inline_claim = Claim()
                inline_claim.set_source("africacheck")
                inline_claim.set_claim(claim_text)
                inline_claim.set_alternate_name(inline_rating)
                inline_claim.set_refered_links(",".join(inline_links))
                inline_claim.set_body(inline_body_text)
                inline_claim.set_tags(", ".join(tags))
                inline_claim.set_date(global_date_str)
                inline_claim.set_url(url)
                if author:
                    inline_claim.set_author(author.get_text())
                inline_claim.set_title(global_title_text)

                local_claims.append(inline_claim)

        else:
            # body
            body = parsed_claim_review_page.find("div", {"id": "main"})
            claim.set_body(body.get_text())

            # related links
            divTag = parsed_claim_review_page.find("div", {"id": "main"})
            related_links = []
            for link in divTag.findAll('a', href=True):
                related_links.append(link['href'])
            claim.set_refered_links(",".join(related_links))

        local_claims.append(claim)

        return local_claims


def get_text_and_links_until_next_header(contents: List[Tag], current_index) -> (Tag, List[str], int):
    links = []  # type : List[str]
    current_element = contents[current_index]
    text = ""
    if not isinstance(current_element, NavigableString):
        text = current_element.text
        for link in current_element.findAll('a', href=True):
            links.append(link['href'])
    while current_element.name != "h2" and current_index < len(contents) - 1:
        current_index += 1
        current_element = contents[current_index]
        if not isinstance(current_element, NavigableString):
            for link in current_element.findAll('a', href=True):
                links.append(link['href'])
            text += current_element.text

    return text, links, current_index


def forward_until_inline_rating(contents: List[Tag], current_index) -> int:
    current_element = contents[current_index]

    if isinstance(current_element, NavigableString):
        div_rating = None
    else:
        div_rating = current_element.find("div", {"class", "inline-rating"})

    while (not div_rating or "inline-rating" not in div_rating['class']) and current_index < len(contents) - 1:
        current_index += 1
        current_element = contents[current_index]
        if isinstance(current_element, NavigableString):
            div_rating = None
        else:
            div_rating = current_element.find("div", {"class", "inline-rating"})

    return current_index
