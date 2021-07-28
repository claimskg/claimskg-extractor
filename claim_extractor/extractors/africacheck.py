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

        url = "https://africacheck.org/search?rt_bef_combine=created_DESC&sort_by=created&sort_order=DESC&page=" + str(page_number)
        
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

        claim_.set_rating(str(re.sub('[^A-Za-z0-9 -]+', '', truth_rating)).lower().strip())

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
        return ["https://africacheck.org/search?rt_bef_combine=created_DESC&sort_by=created&sort_order=DESC&page=0"]
        

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        last_page_link = parsed_listing_page.findAll("a", {"title": "Go to last page"})[0]['href']
        max_page = int(last_page_link.replace("?rt_bef_combine=created_DESC&sort_by=created&sort_order=DESC&search_api_fulltext=&sort_bef_combine=created_DESC&page=",""))
        return max_page

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = self.extract_urls(parsed_listing_page)
        for page_number in tqdm(range(0, number_of_pages)):
            # each page 9 articles:
            if ((page_number*9) + 18 >= self.configuration.maxClaims):
                break
            #url = "https://africacheck.org/latest-reports/page/" + str(page_number) + "/"
            url = "https://africacheck.org/search?rt_bef_combine=created_DESC&sort_by=created&sort_order=DESC&page=" + str(page_number)
            page = caching.get(url, headers=self.headers, timeout=5)
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls += self.extract_urls(current_parsed_listing_page)
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = list()
        links = parsed_listing_page.findAll("div", {"class": "node__content"})
        for anchor in links:
            anchor = anchor.find('a', href=True)
            url = "https://africacheck.org" + str(anchor['href'])
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
        date = parsed_claim_review_page.find("span", {"class": "published"}).next
        global_date_str = ""
        if date:
            # global_date_str = search_dates(date['datetime'].split(" ")[0])[0][1].strftime("%Y-%m-%d")
            global_date_str = search_dates(date)[0][1].strftime("%Y-%m-%d")
            claim.set_date(global_date_str)

        # author
        author = parsed_claim_review_page.find("div", {"class": "author-details"})
        if author:
            claim.set_author(author.get_text())

        if parsed_claim_review_page.select( 'div.author-details > a > h4' ):
                for child in parsed_claim_review_page.select( 'div.author-details > a > h4' ):
                    try:
                        claim.author = child.get_text()
                        continue
                    except KeyError:
                        print("KeyError: Skip")

        if parsed_claim_review_page.select( 'div.author-details > a' ):
                for child in parsed_claim_review_page.select( 'div.author-details > a' ):
                    try:
                        claim.author_url = child['href']
                        continue
                    except KeyError:
                        print("KeyError: Skip")

        # tags
        tags = []

        for tag in parsed_claim_review_page.findAll('meta', {"property": "article:tag"}):
            tags.append(tag["content"])
        claim.set_tags(", ".join(tags))
       
        # claim
        entry_section = parsed_claim_review_page.find("section", {"class", "cell"}) 
        verdict_box = parsed_claim_review_page.find("div", {"class", "article-details__verdict"})
        
        if verdict_box and len(verdict_box) > 0 and "Verdict" in verdict_box.text:
            report_claim_div = parsed_claim_review_page.find("div", {"class": "field--name-field-claims"})
            if report_claim_div:
                claim.set_claim(report_claim_div.get_text())
            else:
                claim.set_claim(claim.title)
            
            # rating
            inline_ratings = parsed_claim_review_page.findAll("div", {"class", "rating"})

            if inline_ratings:
                if (hasattr( inline_ratings[0], 'class')):
                    try:
                        if ('class' in inline_ratings[0].attrs):
                            if (inline_ratings[0].attrs['class'][1]):
                                rating_tmp = inline_ratings[0].attrs['class'][1]
                                claim.rating = rating_tmp.replace('rating--','').replace("-","").capitalize()
                    except KeyError:
                        print("KeyError: Skip")
        else:
            # alternative rating (If there is no article--aside box with verdict)    
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

            # If still no rathing value, try to extract from picture name
            if (global_truth_rating == ""):
                filename =""
                if parsed_claim_review_page.select( 'div.hero__image > picture' ):
                    for child in parsed_claim_review_page.select( 'div.hero__image > picture' ):
                        # child.contents[1].attrs['srcset']
                        if (hasattr( child, 'contents' )):
                            try:
                                filename=child.contents[1].attrs['srcset']
                                continue
                            except KeyError:
                                print("KeyError: Skip")
                
                if (filename != ""):
                    filename_split = filename.split("/")
                    filename_split = filename_split[len(filename_split)-1].split(".png")
                    filename_split = filename_split[0].split("_")
                    if len(filename_split) == 1:
                        global_truth_rating = filename_split[0]
                    else:
                        global_truth_rating = filename_split[len(filename_split)-1]

                claim.set_rating(str(re.sub('[^A-Za-z0-9 -]+', '', global_truth_rating)).lower().strip().replace("pfalse","false").replace("-","").capitalize())
        
        if (not self.rating_value_is_valid(claim.rating)):
            print ("\nURL: " + url)
            print ("\n Rating:" + claim.rating)
            claim.rating = ""
            
         # body
        body = parsed_claim_review_page.find("div", {"class": "article--main"})
        claim.set_body(body.get_text())

        # related links
        related_links = []
        for link in body.findAll('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        if claim.rating:
            return [claim]
        else:
            return []

    def rating_value_is_valid(self, rating_value: str) -> str:
        dictionary = {
            "Correct": "1",
            "Mostlycorrect": "1",
            "Unproven": "1",
            "Misleading": "1",
            "Exaggerated": "1",
            "Understated": "1",
            "Incorrect": "1",
            "Checked": "1",
            "True": "1",
            "False": "1",
            "Partlyfalse": "1",
            "Partlytrue": "1",
            "Fake": "1",
            "Scam": "1",
            "Satire": "1"
        }
    
        if rating_value in dictionary:
                return dictionary[rating_value]
        else:
            return ""

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

