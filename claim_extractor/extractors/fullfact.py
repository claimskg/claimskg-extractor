# -*- coding: utf-8 -*-
import re
from datetime import datetime, timedelta
from typing import List

import dateparser
import contractions
import nltk
from bs4 import BeautifulSoup
from tqdm import tqdm
from nltk import sent_tokenize, word_tokenize, WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.sentiment.util import mark_negation

from claim_extractor import Claim, Configuration
from claim_extractor.extractors import FactCheckingSiteExtractor, caching


class FullfactFactCheckingSiteExtractor(FactCheckingSiteExtractor):

    def __init__(self, configuration: Configuration = Configuration(), ignore_urls: List[str] = None, headers=None,
                 language="eng"):
        super().__init__(configuration, ignore_urls, headers, language)
        self._conclusion_processor = FullfactConclustionProcessor()

    def retrieve_listing_page_urls(self) -> List[str]:
        return ["https://fullfact.org/latest/"]

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        max_page_link = ""
        max_page = int(0)
        if parsed_listing_page.select('body > main > div > div.row.justify-content-center > ul > li.last.page-item > a'):
            for link in parsed_listing_page.select('body > main > div > div.row.justify-content-center > ul > li.last.page-item > a'):
                if hasattr(link, 'href'):
                    max_page_link = link['href']

            max_page = int(max_page_link.replace("?page=", ""))
        return max_page

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) \
            -> List[str]:
        urls = self.extract_urls(parsed_listing_page)
        for page_number in tqdm(range(2, number_of_pages)):
            if 0 < self.configuration.maxClaims < len(urls):
                break
            url = listing_page_url + "?page=" + str(page_number)
            page = caching.get(url, headers=self.headers, timeout=5)
            if page is not None:
                current_parsed_listing_page = BeautifulSoup(page, "lxml")
                urls = urls + self.extract_urls(current_parsed_listing_page)
        return urls

    def extract_urls(self, parsed_listing_page: BeautifulSoup):
        urls = list()
        links = parsed_listing_page.findAll("div", {"class": "card"})

        for anchor in links:
            anchor = anchor.find('a', href=True)
            if "http" in anchor['href']:
                url = str(anchor['href'])
            else:
                url = "https://fullfact.org" + str(anchor['href'])
            max_claims = self.configuration.maxClaims
            if 0 < max_claims <= len(urls):
                break
            if url not in self.configuration.avoid_urls:
                urls.append(url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claims = []
        claim = Claim()

        # url
        claim.url = str(url)

        # souce
        claim.source = "fullfact"

        # title
        title = None
        if parsed_claim_review_page.select('body > main > div > div > section > article > h1'):
            for tmp in parsed_claim_review_page.select('body > main > div > div > section > article > h1'):
                title = tmp.text.strip()
            claim.title = str(title.strip())

        # author
        author_list = []
        author_links = []
        # single author?
        if parsed_claim_review_page.select('article > section.social-media > div > div > ul > li > span > cite'):
            for author_a in parsed_claim_review_page.select('article > section.social-media > div > div > ul > li > span > cite'):
                if hasattr(author_a, 'text'):
                    author_list.append(author_a.text.strip())
                # if hasattr( author_a, 'href' ):
                #    author_list.append( author_a.text.strip() )
                #    author_links.append( author_a.attrs['href'] )
                else:
                    print("no author? https://fullfact.org/about/our-team/")

        claim.author = ", ".join(author_list)
        #claim.author_url = ( ", ".join( author_links ) )

        # date
        datePub = None
        dateUpd = None
        date_str = ""
        # updated?
        if parsed_claim_review_page.select('article > div.published-at'):
            for date_ in parsed_claim_review_page.select('article > div.published-at'):
                if hasattr(date_, 'text'):
                    datePub = date_.text.strip()
                    if "|" in datePub:
                        split_datePub = datePub.split("|")
                        if len(split_datePub) > 0:
                            datePub = split_datePub[0].strip()
                    date_str = dateparser.parse(datePub).strftime("%Y-%m-%d")
                    claim.date_published = date_str
                    claim.date = date_str
                else:
                    print("no date?")

        # Body descriptioon
        text = ""
        if parsed_claim_review_page.select('article > p'):
            for child in parsed_claim_review_page.select('article > p'):
                text += " " + child.text
            body_description = text.strip()
            claim.body = str(body_description).strip()

        # related links (in page body text <p>)
        related_links = []
        if parsed_claim_review_page.select('article > p > a'):
            for link in parsed_claim_review_page.select('article > p > a'):
                try:
                    if hasattr(link, 'href'):
                        if 'http' in link['href']:
                            related_links.append(link['href'])
                        else:
                            related_links.append(
                                "https://fullfact.org" + link['href'])
                except KeyError as e:
                    print("->KeyError: " + str(e))
                    continue
                except IndexError as e:
                    print("->IndexError : " + str(e))
                    continue


        # related links (in Related fact checks)
        if parsed_claim_review_page.select('section.related-factchecks > div > ul > li > a'):
            for link in parsed_claim_review_page.select('section.related-factchecks > div > ul > li > a'):
                try:
                    if hasattr(link, 'href'):
                        if 'http' in link['href']:
                            related_links.append(link['href'])
                        else:
                            related_links.append(
                                "https://fullfact.org" + link['href'])
                except KeyError as e:
                    print("->KeyError: " + str(e))
                    continue
                except IndexError as e:
                    print("->IndexError: " + str(e))
                    continue

        if related_links:
            claim.referred_links = related_links

        # cannot be found on fullfact:
        # self.tags = ""
        # self.author_url = ""
        # self.date_published = ""
        # self.same_as = ""
        # self.rating_value = ""
        # self.worst_rating = ""
        # self.best_rating = ""
        # self.review_author = ""

        # claim # multiple (local) claims: 'article > div > div > div.row.no-gutters.card-body-text > div > div > p' ?
        claim_text_list = []
        claim_text = None
        # rating -> VERDICT: extract_conclusion -> true, false, ...
        claim_verdict_list = []
        claim_verdict = None

        column = "claim"  # or verdict:
        if parsed_claim_review_page.select('body > main > div > div > section > article > div > div > div.row.no-gutters.card-body-text > div > div > p'):
            for p in parsed_claim_review_page.select('body > main > div > div > section > article > div > div > div.row.no-gutters.card-body-text > div > div > p'):
                if hasattr(p, 'text'):
                    if column == "claim":
                        claim_text_list.append(p.text.strip())
                        if claim_text == None:
                            claim_text = p.text.strip()
                        column = "verdict"
                    else:
                        rating_word_list = p.text
                        conclusion_text = self._conclusion_processor.extract_conclusion(
                            rating_word_list)
                        #print ("conclusion_text: " + conclusion_text)
                        rating = str(conclusion_text).replace('"', "").strip()
                        if "." in rating:
                            split_name = rating.split(".")
                            if len(split_name) > 0:
                                rating = split_name[0]
                        claim_verdict_list.append(rating)
                        if claim_verdict == None:
                            claim_verdict = rating

                        column = "claim"

            # First local claim and rating:
            claim.claim = claim_text
            claim.rating = claim_verdict

            # All claims and ratings "comma" separated: get all claims?
            # claim.claim = ", ".join( claim_text_list )
            # claim.rating = ", ".join( verdict_text_list )

            # Create multiple claims from the main one and add change then the claim text and verdict (rating):
            c = 0
            while c <= len(claim_text_list)-1:
                claims.append(claim)
                claims[c].claim = claim_text_list[c]
                claims[c].rating = claim_verdict_list[c]
                c += 1

            # for local_claim in claim_text_list:
            #    claims[claim[len(claim)]] = claims[claim[len(claim)-1]]

        # No Rating? No Claim?
        if not claim.claim or not claim.rating:
            print(url)
            if not claim.rating:
                print("-> Rating cannot be found!")
            if not claim.claim:
                print("-> Claim cannot be found!")
            return []

        # return [claim]
        return claims


class FullfactConclustionProcessor:
    def __init__(self):
        self._vocabulary = {"true": ["correct", "right", "true", "evidence", "accurate", "exact"],
                            "false": ["incorrect", "false", "fake", "wrong", "inaccurate", "untrue"],
                            "mixture": ["uncertain", "ambiguous", "unclear", "unsure", "undetermined"],
                            "opposition_words": ["but", "however"],
                            "negation": ["no", "not", "neither", "nor"],
                            "mix_with_neg": ["quite", "necessarily", "sure", "clear"]}

        stop_words = stopwords.words('english')
        self._stop_words = [
            w for w in stop_words if not w in self._vocabulary["negation"]]

        self._punctuation = [".", ",", "!", ";", "?", "'", "\""]

        self._verb_tags = ["MD", "VB", "VBP"]
        self._wordnet_lemmatizer = WordNetLemmatizer()

    # Fonction qui traite les contractions dans les phrases puis les découpe et met leurs termes en minuscule
    @staticmethod
    def _nettoyage(conclusion):
        phrase = sent_tokenize(conclusion)
        phrase[0] = contractions.fix(phrase[0])
        tokens = word_tokenize(phrase[0])
        tokens = [w.lower() for w in tokens]
        return tokens

    # Fonction qui réduit les mots à leurs racines (mett les verbes à l'infinitif, supprime le "s" du pluriel, etc)
    def _lemmatization(self, tempo):
        tempo = [self._wordnet_lemmatizer.lemmatize(
            word, pos='v') for word in tempo]
        return tempo

    def _remove_stopwords(self, tempo):
        tempo = [w for w in tempo if not w in self._stop_words]
        return tempo

    # Fonction qui détecte les cas tels que (it's correct...however)
    def _detect_opposition(self, indice, tempo, n=False):
        new_tempo = tempo[indice + 1:]
        if n:
            sentence = "".join([" " + i for i in new_tempo])
        else:
            sentence = "".join([" " + i[0] for i in new_tempo])

        for m in self._vocabulary["opposition_words"]:
            if m in sentence:
                return True
        return False

    def _direct_extraction(self, words):
        words = [t for t in words if not t in self._punctuation]

        tempo = nltk.pos_tag(words)
        tempoLematise = self._lemmatization(words)
        tempoL = nltk.pos_tag(tempoLematise)
        i = 0
        if tempoL[-1][0] == "not" and (tempoL[-2][1] in self._verb_tags):
            return "False"

        while i < len(tempo):

            if (tempo[i][0] in self._vocabulary["true"] or tempo[i][0] in self._vocabulary["false"]) and i + 1 != len(
                    tempo) and self._detect_opposition(i, tempo):
                return "Mixture"

            if tempo[i][0] in self._vocabulary["false"]:
                return "False"

            if tempo[i][0] in self._vocabulary["true"]:
                return "True"

            if tempo[i][0] in self._vocabulary["mixture"]:
                return "Mixture"

            i += 1
        return "Other"

    def _indirect_negation(self, tempo):
        words = mark_negation(tempo)
        neg = [w.replace("_NEG", "") for w in words if w.endswith("_NEG")]
        i = 0
        for n in neg:
            if (n in self._vocabulary["true"] or n in self._vocabulary["false"]) and i + 1 != len(
                    neg) and self._detect_opposition(i, neg,
                                                     n=True):
                return "Mixture"

            if n in self._vocabulary["mix_with_neg"]:
                return "Mixture"

            if n in self._vocabulary["true"]:
                return "False"

            if n in self._vocabulary["false"]:
                return "True"

            i += 1

        return "Other"

    def extract_conclusion(self, conclusion):
        words = FullfactConclustionProcessor._nettoyage(conclusion)
        result = self._indirect_negation(words)
        if result == "Other":
            result = self._direct_extraction(words)
        return result
