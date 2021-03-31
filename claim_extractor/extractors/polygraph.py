# -*- coding: utf-8 -*-
from typing import List

from bs4 import BeautifulSoup
from tqdm import tqdm

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


class PolygraphFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        super().__init__(configuration, language="rus")
        # self.date_regexp = re.compile("^([0-9]{4})/([0-9]{2})/([0-9]{2})*") #date:annee, mois, jour

    def retrieve_listing_page_urls(self) -> List[str]:
        return ["https://www.polygraph.info/z/20382?p=1"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        count = 5
        url = "https://www.polygraph.info/z/20382?p=" + str(count + 1)
        result = caching.get(url, headers=self.headers, timeout=10)
        if result:
            while result:
                count += 1
                url = "https://www.polygraph.info/z/20382?p=" + str(count)
                result = caching.get(url, headers=self.headers, timeout=10)
                if result:
                    parsed = BeautifulSoup(result, self.configuration.parser_engine)
                    articles = parsed.findAll("li", {"class": "fc__item"})
                    if not articles or len(articles) == 0:
                        break
        else:
            count -= 1

        return count - 1

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        # lien de la premiere page -> liste de textes
        urls = self.extract_urls(parsed_listing_page)
        # parcours from 2 to end
        for page_number in tqdm(range(2, number_of_pages + 1)):
            url = "https://www.polygraph.info/z/20382?p=" + str(page_number) + "/"
            # load from cache (download if not exists, sinon load )
            page = caching.get(url, headers=self.headers, timeout=5)
            if page:
                # parser avec BeautifulSoup la page
                current_parsed_listing_page = BeautifulSoup(page, "lxml")
                # extriare les liens dans cette page et rajoute dans urls
                urls += self.extract_urls(current_parsed_listing_page)
            else:
                break
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = list()
        # when simply findAll(a, class=title), same href exists two times (title and title red)
        links = parsed_listing_page.findAll(lambda tag: tag.name == 'a' and
                                                        tag.get('class') == ['title'])
        for anchor in links:
            url = "https://www.polygraph.info" + str(anchor['href'])
            max_claims = self.configuration.maxClaims
            if 0 < max_claims <= len(urls):
                break
            if url not in self.configuration.avoid_urls:
                urls.append(url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claim = Claim()
        claim.set_url(url)
        claim.set_source("polygraph")

        # title
        title = parsed_claim_review_page.find("h1", {"class": "title pg-title"})
        claim.set_title(title.text.replace(";", ","))

        # date
        full_date = parsed_claim_review_page.find("time")['datetime'].split("T")
        claim.set_date(full_date[0])

        # body
        # body = parsed_claim_review_page.find('div', {"id":"article-content"}).find_all('p')
        # for b in body:
        #    claim.set_body(b.get_text())
        body = parsed_claim_review_page.find("div", {"id": "article-content"})
        claim.set_body(body.get_text())

        # related related_links
        related_links = []
        for link in body.findAll('a', href=True):
            related_links.append(link['href'])
        claim.set_refered_links(related_links)

        claim.set_claim(claim.title)

        # author
        author = parsed_claim_review_page.find('h4', {"class": "author"})
        claim.set_author(author.text)

        # rating
        rating = parsed_claim_review_page.find('div', {"class": "verdict"}).find_all('span')[1]
        claim.set_rating(rating.text)

        return [claim]
