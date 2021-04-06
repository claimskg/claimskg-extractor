# -*- coding: utf-8 -*-
import re
from datetime import datetime, timedelta
from typing import List

import contractions
import nltk
from bs4 import BeautifulSoup
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
        today = datetime.today()
        d = ldate = today
        lim = datetime.strptime('2019-06-01', "%Y-%m-%d")  # Date where the script will stop the scraping
        i = 0
        delta = timedelta(days=3)
        urls = list()
        while d > lim:
            i = i + 1
            url = 'http://web.archive.org/web/' + d.strftime('%Y%m%d') + '/https://fullfact.org/'

            r = caching.head(url, headers=self.headers, timeout=10)

            try:
                if r['status_code'] != 200:
                    d = d - delta
                    continue

                dre = re.compile("http://web.archive.org/web/([0-9]+)/https://fullfact.org/")
                date = dre.match(r['url']).group(1)  # date of the link that is being processed
                date = datetime.strptime(date[:8], "%Y%m%d")

                if (date.day == ldate.day and date.month == ldate.month):
                    print(date.strftime('%Y-%m-%d'))
                    d = d - delta  # d is a date that discrements by a day each
                    continue
            except Exception as e:
                d = d - delta
                continue

            print('Added home page of ' + date.strftime('%Y-%m-%d'))
            urls.append(r['url'])
            ldate = date  # ldate is the date of the last link that was added
            d = date - delta

        return urls

    def find_page_count(self, parsed_listing_page: BeautifulSoup) -> int:
        return -1

    def retrieve_urls(self, parsed_listing_page: BeautifulSoup, listing_page_url: str, number_of_pages: int) -> List[
        str]:
        urls = []
        div = parsed_listing_page.find('div', id='mostRecent')
        elems = div.findAll('li')
        for elem in elems:
            url = elem.find('a')['href'][20:]
            n = len(self.seen)
            self.seen.add(url)
            if len(self.seen) == n:
                continue
            urls.append(url)
        return urls

    def extract_claim_and_review(self, parsed_claim_review_page: BeautifulSoup, url: str) -> List[Claim]:
        claims = []

        categories = parsed_claim_review_page.find('ol', {'class': 'breadcrumb col-xs-12'})
        elems = categories.findAll('a')
        keywords = []
        for elem in elems:
            keywords.append(elem.text)

        date = parsed_claim_review_page.find("p", {"class": "date"})
        date_value = ""
        if date:
            date_value = date.find("span").get_text()

        # extraction of brief claims
        brief_conclusion = parsed_claim_review_page.find('div', {"id": "briefClaimConclusion"})
        box_panel = brief_conclusion.find('div', {"class": "box-panel"})
        conclusion_divs = box_panel.findAll('div')
        for conclusion_div in conclusion_divs:
            try:
                claim = Claim()
                claim.set_url(url)
                claim.set_source("fullfact")
                claim_text = conclusion_div.find('div', {"class": "col-xs-12 col-sm-6 col-left"}).find('p').text
                conclusion_text = conclusion_div.find('div', {"class": "col-xs-12 col-sm-6 col-right"}).find('p').text
                conclusion_text = self._conclusion_processor.extract_conclusion(conclusion_text)

                claim.set_claim(claim_text)
                claim.set_rating(conclusion_text)
                claim.set_tags(','.join(keywords))
                claim.set_date_published(date_value)
                claims.append(claim)
            except Exception as e:
                continue

        # Extraction of quotes, which often contain claims on pages without
        quotes = parsed_claim_review_page.findAll('blockquote')

        if len(claims) == 0 or len(quotes) == 0:
            return claims

        for quote in quotes:
            claim = Claim()
            claim.set_url(url)
            claim.set_source("fullfact")
            try:
                p = quote.findAll('p')

                if len(p) == 1:  # if there one paragraph then there is no author nor date
                    claim.set_claim(p[0].text)
                    claim.set_tags(','.join(keywords))
                    claims.append(claim)
                    continue

                claim_text = ''
                for x in p[:-1]:  # Sometimes the quote is made of 2 paragraphs or more
                    claim_text = x.text

                if len(claim_text) < 4:  # if it's too small it is not a claim
                    continue

                p = p[-1]  # last paragraph always mentions the author and the date
                author = p.text.split(',')[:-1]  # and there is always a semicolon seperating the two
                date = p.text.split(',')[-1]

                while not claim_text[0].isalnum():
                    claim_text = claim_text[1:]

                while not claim_text[-1].isalnum():
                    claim_text = claim_text[:-1]

                claim.set_claim(claim_text)
                claim.set_author(''.join(author))
            except Exception:
                continue

            try:
                a = p.find('a')  # usually the date is mentioned with the link where the claim was made
                date = datetime.strptime(a.text, '%d %B %Y').strftime("%Y-%m-%d")
                claim.set_refered_links(a['href'])
                claim.set_date(date)
            except Exception as e:
                try:
                    date = datetime.strptime(date[1:-1], ' %d %B %Y').strftime("%Y-%m-%d")
                    claim.set_date(date)
                except Exception as e:
                    pass
            claim.set_tags(keywords)
            claims.append(claim)

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
        self._stop_words = [w for w in stop_words if not w in self._vocabulary["negation"]]

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
        tempo = [self._wordnet_lemmatizer.lemmatize(word, pos='v') for word in tempo]
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
