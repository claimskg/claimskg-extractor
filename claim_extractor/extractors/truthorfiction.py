# -*- coding: utf-8 -*-
import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateparser.search import search_dates

from claim_extractor import Claim


def get_all_claims(criteria):
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

    # print criteria.maxClaims
    # performing a search by each letter, and adding each article to a urls_ var.
    now = datetime.datetime.now()
    urls_ = {}
    types = ["a"]
    last_page = []
    for type_ in types:
        for page_number in range(1, 500):
            if 0 < criteria.maxClaims <= len(urls_):
                break
            # url="http://www.politifact.com/truth-o-meter/rulings/"+str(type_)+"/?page="+str(page_number)
            url = "https://www.truthorfiction.com/page/" + str(page_number) + "/?s=" + str(type_)
            page = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(page.text, "lxml")

            links = soup.findAll("h2", {"class": "grid-title"})
            if (len(links) > 0) and (links != last_page):
                for anchor in links:
                    anchor = anchor.find('a', href=True)
                    ind_ = str(anchor['href'])
                    if ind_ not in list(urls_.keys()):
                        if 0 < criteria.maxClaims <= len(urls_):
                            break
                        if ind_ not in criteria.avoid_url:
                            urls_[ind_] = anchor.get_text()
                last_page = links
            else:
                break

    claims = []
    index = 0
    # visiting each article's dictionary and extract the content.
    for url, title_claim in urls_.items():
        print(str(index) + "/" + str(len(list(urls_.keys()))) + " extracting " + str(url))
        index += 1

        url_complete = str(url)

        try:
            page = requests.get(url_complete, headers=headers, timeout=5)
            soup = BeautifulSoup(page.text, "lxml")
            soup.prettify("utf-8")

            claim_ = Claim()
            claim_.setUrl(url_complete)
            claim_.setSource("truthorfiction")

            if (criteria.html):
                claim_.setHtml(soup.prettify("utf-8"))

            title = title_claim[:title_claim.rfind("-")]
            claim_.setTitle(title)

            # date

            date_ = soup.find('div', {"class": "post-box-meta-single"}).find("span")
            if date_:
                date_str = search_dates(date_.text.replace(",", ""), settings={'DATE_ORDER': 'MDY'})[0][1].strftime(
                    "%Y-%m-%d")
                claim_.setDate(date_str)

            # body
            body = soup.find("div", {"class": "inner-post-entry"})
            claim_.setBody(body.get_text())

            # related links
            divTag = soup.find("div", {"class": "inner-post-entry"})
            related_links = []
            for link in divTag.findAll('a', href=True):
                related_links.append(link['href'])
            claim_.set_refered_links(related_links)

            claim_.setClaim(title)

            tags = []

            for tag in soup.findAll('a', {"rel": "tag"}, href=True):
                tag_str = tag.text
                tags.append(tag_str)
            claim_.set_tags(", ".join(tags))

            claims.append(claim_.generate_dictionary())
        except:
            print("Error ->" + str(url_complete))

    # creating a pandas dataframe
    pdf = pd.DataFrame(claims)
    return pdf


class TruthorfictionFactCheckingSiteExtractor(FactCheckingSiteExtractor):

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
            -> Set[str]:
        urls = self.extract_urls(parsed_listing_page)
        for page_number in tqdm(range(2, number_of_pages)):
            url = "http://factscan.ca/page/" + page_number + "/"
            page = caching.get(url, headers=self.headers, timeout=5)
            current_parsed_listing_page = BeautifulSoup(page, "lxml")
            urls = set.union(urls, self.extract_urls(current_parsed_listing_page))
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = set()
        links = parsed_listing_page.findAll("h1", {"class": "post-title entry-title home-feed-title"})
        for anchor in links:
            anchor = anchor.find('a', href=True)
            url = str(anchor['href'])
            max_claims = self.configuration.maxClaims
            if 0 < max_claims <= len(urls):
                break
            if url not in self.configuration.avoid_urls:
                urls.add(url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> Claim:
        claim = Claim()
        claim.setUrl(url)
        claim.setSource("factscan")

        json_ = None
        if parsed_claim_review_page.find("script", {"type": "application/ld+json"}):
            json_ = parsed_claim_review_page.find("script", {"type": "application/ld+json"}).get_text()

        def parse_wrong_json(json_, left, right):
            if json_:
                if len(json_.split(left)) > 0:
                    return json_.split(left)[1].split(right)[0]
            else:
                return None

        # title
        title = parsed_claim_review_page.find("meta", {"property": "og:title"})['content']
        claim.setTitle(title)

        # date
        date_ = parsed_claim_review_page.find('meta', {"property": "article:published_time"})
        if date_:
            date_str = search_dates(date_['content'].split("T")[0])[0][1].strftime("%Y-%m-%d")
            claim.setDate(date_str)

        # rating
        claim.set_rating_value(parse_wrong_json(json_, '"ratingValue":', ","))
        claim.setWorstRating(parse_wrong_json(json_, '"worstRating":', ","))
        claim.set_best_rating(parse_wrong_json(json_, '"bestRating":', ","))
        claim.setAlternateName(parse_wrong_json(json_, '"alternateName":', ","))

        # when there is no json
        if not claim.alternate_name:
            if parsed_claim_review_page.find("div", {"class": "fact-check-icon"}):
                if parsed_claim_review_page.find("div", {"class": "fact-check-icon"}).find('img'):
                    claim_str = \
                        parsed_claim_review_page.find("div", {"class": "fact-check-icon"}).find('img')['alt'].split(
                            ":")[1]
                    claim.alternate_name = claim_str

        # body
        body = parsed_claim_review_page.find("div", {"class": "entry-content"})
        claim.setBody(body.get_text())

        # author
        author = parsed_claim_review_page.find("div", {"class": "sharethefacts-speaker-name"})
        if author:
            claim.setAuthor(author.get_text())

        # same_as
        claim.setSameAs(parse_wrong_json(json_, '"sameAs": [', "]"))

        # related links
        divTag = parsed_claim_review_page.find("div", {"class": "entry-content"})
        related_links = []
        for link in divTag.findAll('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        if parsed_claim_review_page.find("div", {"class": "sharethefacts-statement"}):
            claim.setClaim(parsed_claim_review_page.find("div", {"class": "sharethefacts-statement"}).get_text())
        else:
            claim.setClaim(claim.title)

        tags = []

        for tag in parsed_claim_review_page.findAll('meta', {"property": "article:tag"}):
            tags.append(tag["content"])
        claim.set_tags(", ".join(tags))

        return claim
