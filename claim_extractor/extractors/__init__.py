import re
from abc import ABC, abstractmethod
from typing import List

import pandas
from bs4 import BeautifulSoup
from tqdm import tqdm

from claim_extractor import Configuration, Claim
from claim_extractor.extractors import caching
from claim_extractor.extractors.caching import get_claim_from_cache, cache_claim

MATCH_ALL = r'.*'


def like(string):
    """
    Return a compiled regular expression that matches the given
    string with any prefix and postfix, e.g. if string = "hello",
    the returned regex matches r".*hello.*"
    """
    string_ = string
    if not isinstance(string_, str):
        string_ = str(string_)
    regex = MATCH_ALL + re.escape(string_) + MATCH_ALL
    return re.compile(regex, flags=re.DOTALL)


def find_by_text(soup, text, tag, **kwargs):
    """
    Find the tag in soup that matches all provided kwargs, and contains the
    text.

    If no match is found, return None.
    If more than one match is found, raise ValueError.
    """
    elements = soup.find_all(tag, **kwargs)
    matches = []
    for element in elements:
        if element.find(text=like(text)):
            matches.append(element)
    if len(matches) == 0:
        return None

    return matches


class FactCheckingSiteExtractor(ABC):

    seen = set()

    def __init__(self, configuration: Configuration = Configuration(), ignore_urls: List[str] = None, headers=None,
                 language="eng"):
        if headers is None:
            self.headers = {
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/53.0.2785.143 Safari/537.36'}
        if ignore_urls is None:
            ignore_urls = list()
        self.ignore_urls = ignore_urls
        self.configuration = configuration
        self.ignore_urls = configuration.avoid_urls
        self.language = language
        self.failed_log = open(self.__class__.__name__ + "_extraction_failed.log", "w")

    def get_all_claims(self):
        claims = []  # type : List[Claim]

        listing_pages = self.retrieve_listing_page_urls()
        for listing_page_url in listing_pages:
            print("Fetching listing pages from " + listing_page_url)
            page = caching.get(listing_page_url, headers=self.headers, timeout=5)
            if not page:
                continue
            parsed_listing_page = BeautifulSoup(page, self.configuration.parser_engine)
            number_of_pages = self.find_page_count(parsed_listing_page)
            if number_of_pages and number_of_pages < 0:
                number_of_pages = None

            urls = self.retrieve_urls(parsed_listing_page, listing_page_url, number_of_pages)

            print("Extracting claims listed in " + listing_page_url)
            for url in tqdm(urls):
                try:
                    if "http" in url:
                        review_page = caching.get(url, headers=self.headers, timeout=6)
                        if review_page:
                            parsed_claim_review_page = BeautifulSoup(review_page, self.configuration.parser_engine)
                            claim = get_claim_from_cache(url)
                            if not claim:
                                local_claims = self.extract_claim_and_review(parsed_claim_review_page, url)
                                if len(local_claims) > 1:
                                    for claim in local_claims:
                                        claims.append(claim.generate_dictionary())
                                elif len(local_claims) == 1 and local_claims[0]:
                                    claims.append(local_claims[0].generate_dictionary())
                                    cache_claim(local_claims[0])
                                else:
                                    self.failed_log.write(url + "\n")
                                    self.failed_log.flush()
                            else:
                                claims.append(claim.generate_dictionary())
                except ConnectionError:
                    pass
        self.failed_log.close()
        return pandas.DataFrame(claims)

    @abstractmethod
    def retrieve_listing_page_urls(self) -> List[str]:
        """
            Abstract method. Retrieve the URLs of pages that allow access to a paginated list of claim reviews. This
            concerns some sites where all the claims are not listed from a single point of access but first
            categorized by another criterion (e.g. on politifact there is a separate listing for each possible rating).
            :return: Return a list of listing page urls
        """

    @abstractmethod
    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        """
        A listing page is paginated and will sometimes contain information pertaining to the maximum number of pages
        there are. For sites that do not have that information, please return a negative integer or None
        :param parsed_listing_page:
        :return: The page count if relevant, otherwise None or a negative integer
        """
        pass

    @abstractmethod
    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        pass

    @abstractmethod
    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        pass
