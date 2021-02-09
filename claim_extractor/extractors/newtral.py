# -*- coding: utf-8 -*-
import json
import re
from typing import List

import regex
from bs4 import BeautifulSoup

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


class NewtralFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration):
        super().__init__(configuration)

    def retrieve_listing_page_urls(self) -> List[str]:
        return ["https://www.newtral.es/zona-verificacion/fact-check/"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        return -1

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        query_url = "https://www.newtral.es/wp-json/wp/v2/posts?per_page=100&offset={offset}&categories=1" + \
                    "&exclude=80729%2C79970%2C78262%2C78455%2C77275%2C77315%2C77161%2C76907%2C76298" + \
                    "%2C75434%2C74706%2C74103%2C74062&_locale=user"

        urls = []

        json_output = caching.get(query_url.format(offset=0), headers=self.headers, timeout=5)
        offset = 0

        while json_output.strip() != "[]":
            pages = json.loads(json_output)
            for page in pages:
                urls.append(page['link'])
            offset += 100
            json_output = caching.get(query_url.format(offset=offset), headers=self.headers, timeout=5)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claim = Claim()
        claim.set_url(url)
        claim.set_source("newtral")

        title = parsed_claim_review_page.find("meta", attrs={'property': 'og:title'})['content']
        title = title.strip().split("|")[0]
        claim.set_title(title)

        dospunto = re.search(r'(: «)', title)
        dospunt = re.search(r'(: “)', title)

        if dospunto:
            claim_a = title.split(":")
            auteur = claim_a[0].strip()
            claim.author = auteur
            # print ("auteur:" , auteur)
            claim_text = claim_a[1].strip("« »")
            claim.claim = claim_text

        elif dospunt:
            claim_b = title.split(":")
            auteur = claim_b[0].strip()
            # print ("auteur:" , auteur)
            claim.author = auteur
            claim_text = claim_b[1].strip(": “ ”")
            # print ("claim :", claim)
            claim.claim = claim_text
        else:
            pass

        tags = parsed_claim_review_page.find_all("meta", attrs={'property': 'article:tag'})
        tag_list = []
        for tag in tags:
            tag_text = tag['content']
            tag_list.append(tag_text)
        claim.set_tags(",".join(tag_list))

        published = parsed_claim_review_page.find("meta", attrs={'property': 'article:published_time'})[
            'content']
        claim.date_published = published.strip()

        entry_content = parsed_claim_review_page.find("div", attrs={'class': 'entry-content'})

        intro = parsed_claim_review_page.find("div", attrs={'class': 'c-article__intro'})
        if intro is None:
            intro_rating_p = entry_content.find("em")
            if intro_rating_p is None:
                intro_rating_p = entry_content.find("p")
            if intro_rating_p is None:
                intro_rating_p = entry_content.find("div")
        else:
            intro_rating_p = intro.p
        rating_in_image = False
        if intro_rating_p is None:  # Rating in image...
            rating_in_image = True
            rating_text = ""
        else:
            rating_text = intro_rating_p.get_text()

        rating_re_es_falso = regex.compile(
            r"(La afirmación es|La afirmación es una|La declaración es|Es|El dato es" + \
            "|La comparación de Colau es)? ?([\p{Lu}| ]+)(\.| –|,| )")

        es_falso_match = rating_re_es_falso.match(rating_text)
        if es_falso_match is not None and es_falso_match.group(2) is not None:
            rating_text = es_falso_match.group(2)
        else:
            if not rating_in_image:
                is_there_b = intro_rating_p.find('b')
                if is_there_b is not None:
                    rating_text = is_there_b.text
                else:
                    is_there_strong = intro_rating_p.find("strong")
                    if is_there_strong is not None:
                        rating_text = is_there_strong.text
                    else:
                        pass

        claim.rating = rating_text

        author_span = parsed_claim_review_page.find("span", attrs={'class': 'c-article__author'})
        author_a = author_span.find("a")
        author_url = author_a['href']
        author_text = author_a.text
        author_text = re.sub('Por', '', author_text).strip()
        claim.author_url = author_url
        claim.review_author = author_text

        # Recuperation du texte de l'article

        entry_text = ""
        body_t = entry_content.find_all('p')
        body = [text.text.strip() for text in body_t]
        entry_text += " ".join(body) + "\n"
        claim.body = entry_text

        # Recuperation des liens dans le texte de l'article
        links = [link['href'] for link in entry_content.find_all('a', href=True)]
        claim.referred_links = links

        # else:
        #     title = container.h3.text
        #     titles.append(title)
        #     # print("title", title)
        #     claim_c = hd.h1.text.split(":")
        #     claim_d = hd.h1.text.strip()
        #
        #     if claim_c:
        #         auteur = claim_c[0].strip()
        #         auteurs.append(auteur)
        #         print("auteur:", auteur)
        #         claim = claim_c[1].strip("« »")
        #         claims.append(claim)
        #         # print ("claim :", claim)
        #     # else  :
        #     # print (claim_d)
        #

        return [claim]
