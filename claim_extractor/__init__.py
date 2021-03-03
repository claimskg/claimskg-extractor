from typing import Dict


class Claim:

    def __init__(self):
        """
        Default constructor, see other constructor to build object from dictionary
        """
        self.source = ""
        """The name of the fack checking site, should match the name of the extractor"""

        self.claim = str("")
        """The text of the claim (almost always different from the title of the page!)"""

        self.body = str("")
        """Text of the claim review extracted from the fact checkin site"""

        self.referred_links = ""
        """Links that appear in the body of the claim review in support of various statements."""

        self.title = str("")
        """Titre of the claim review page, often different from the claim, e.g. a reformulation with more context."""

        self.date = ""
        """Date on which the claim review was written"""

        self.url = ""
        """URL of the claim review. Mandatory."""

        self.tags = ""
        """List of tags/keywords extracted from the fact checking site when available, strings separated by commas"""

        self.author = ""
        """Name of the author of the claim (the claimer)."""

        self.author_url = ""
        """Webpage URL associated with the author of the claim review."""

        self.date_published = ""
        """Date on which the claim was made. Not always available in fact checking sites. Often extracted from 
        free text. Optional, but please include it if the information is available in the fact checking site."""

        self.same_as = ""
        """URL of claim reviews that are marked as identical. Only for fact checkin sites that have a list of 
        associated claim reviews. Optional."""

        self.rating_value = ""
        """Numerical value for the truth rating, only for fact checking sites that include this information in the
        meta tags following the schema.org specification. Optional."""

        self.worst_rating = ""
        """Numerical value for worst rating on the scale, only for fact checking sites that include this information in the
        meta tags following the schema.org specification. Optional."""

        self.best_rating = ""
        """Numerical value for best rating on the scale, only for fact checking sites that include this information in the
        meta tags following the schema.org specification. Optional."""

        self.rating = ""
        """Truth rating (text) for the claim extracted from the fact checking site. Mandatory."""

        self.claim_entities = ""
        """Named entities extracted from the text of the claim encoded in JSON, optional and deprecated,
        this will be done in the claimskg generator"""

        self.body_entities = ""
        """Named entities extracted from the body of the claim review encoded in JSON, optional and deprecated,
        this will be done in the claimskg generator"""

        self.keyword_entities = ""
        """Named entities extracted from the keywords associated with the claim review encoded in JSON, optional and deprecated,
        this will be done in the claimskg generator"""

        self.author_entities = ""
        """Named entities extracted from the name of the claimer (author of the claim) encoded in JSON, optional and deprecated,
        this will be done in the claimskg generator"""

        self.review_author = ""
        """Author of the review of the claim on the fact checking site (not the claimer!)"""

        self.related_links = []

    def generate_dictionary(self):
        if isinstance(self.referred_links, list):
            self.referred_links = ",".join(self.referred_links)
        dictionary = {'rating_ratingValue': self.rating_value, 'rating_worstRating': self.worst_rating,
                      'rating_bestRating': self.best_rating, 'rating_alternateName': self.rating,
                      'creativeWork_author_name': self.author, 'creativeWork_datePublished': self.date_published,
                      'creativeWork_author_sameAs': self.same_as, 'claimReview_author_name': self.source,
                      'claimReview_author_url': self.author_url, 'claimReview_url': self.url,
                      'claimReview_claimReviewed': self.claim, 'claimReview_datePublished': self.date,
                      'claimReview_source': self.source, 'claimReview_author': self.review_author,
                      'extra_body': self.body.replace("\n", ""), 'extra_refered_links': self.referred_links,
                      'extra_title': self.title, 'extra_tags': self.tags,
                      'extra_entities_claimReview_claimReviewed': self.claim_entities,
                      'extra_entities_body': self.body_entities, 'extra_entities_keywords': self.keyword_entities,
                      'extra_entities_author': self.author_entities, 'related_links': ",".join(self.related_links)}
        return dictionary

    @classmethod
    def from_dictionary(cls, dictionary: Dict[str, str]) -> 'Claim':
        """
        Build claim instance from dictionary generated by the generate_dictionary method, mainly used for round tripping
        from cache.
        :param dictionary: The dictionary generated by generate_dictionary
        """
        claim = Claim()
        if 'claimReview_author_name' in dictionary.keys():
            claim.source = dictionary['claimReview_author_name']
        else:
            claim.source = ""
        claim.claim = dictionary["claimReview_claimReviewed"]
        claim.body = dictionary['extra_body']
        claim.referred_links = dictionary['extra_refered_links']
        claim.title = dictionary['extra_title']
        claim.date = dictionary['claimReview_datePublished']
        claim.url = dictionary['claimReview_url']
        claim.tags = dictionary['extra_tags']
        claim.author = dictionary['creativeWork_author_name']
        claim.date_published = dictionary['creativeWork_datePublished']
        claim.same_as = dictionary['creativeWork_author_sameAs']
        claim.author_url = dictionary['claimReview_author_url']
        claim.rating_value = dictionary['rating_ratingValue']
        claim.worst_rating = dictionary['rating_worstRating']
        claim.best_rating = dictionary['rating_bestRating']
        claim.rating = dictionary['rating_alternateName']
        claim.related_links = dictionary['related_links']

        return claim

    def set_rating_value(self, string_value):
        if string_value:
            string_value = str(string_value).replace('"', "")
            self.rating_value = string_value
        return self

    def set_worst_rating(self, str_):
        if str_:
            str_ = str(str_).replace('"', "")
            self.worst_rating = str_
        return self

    def set_best_rating(self, str_):
        if str_:
            str_ = str(str_).replace('"', "")
            self.best_rating = str_
        return self

    def set_rating(self, alternate_name):
        self.rating = str(alternate_name).replace('"', "").strip()
        # split sentence

        if "." in self.rating:
            split_name = self.rating.split(".")
            if len(split_name) > 0:
                self.rating = split_name[0]

        return self

    def set_source(self, str_):
        self.source = str_
        return self

    def set_author(self, str_):
        self.author = str_
        return self

    def set_same_as(self, str_):
        if str_ is not None:
            self.same_as = str_
        return self

    def set_date_published(self, str_):
        self.date_published = str_
        return self

    def set_claim(self, str_):
        self.claim = str(str_).strip()
        return self

    def set_body(self, str_):
        self.body = str(str_).strip()
        return self

    def set_refered_links(self, str_):
        self.referred_links = str_
        return self

    def set_title(self, str_):
        self.title = str(str_).strip()
        return self

    def set_date(self, str_):
        self.date = str_
        return self

    def set_url(self, str_):
        self.url = str(str_)
        return self

    def set_tags(self, str_):
        self.tags = str_

    def add_related_link(self, link):
        self.related_links.append(link)

    def add_related_links(self, links):
        self.related_links.extend(links)


class Configuration:

    def __init__(self):
        self.maxClaims = 0
        self.within = "15mi"
        self.output = "output.csv"
        self.website = ""
        self.until = None
        self.since = None
        self.html = False
        self.entity = False
        self.input = None
        self.rdf = None
        self.avoid_urls = []
        self.update_db = False
        self.entity_link = False
        self.normalize_credibility = True
        self.parser_engine = "lxml"

    def setSince(self, since):
        self.since = since
        return self

    def setUntil(self, until):
        self.until = until
        return self

    def setMaxClaims(self, maxClaims):
        self.maxTweets = maxClaims
        return self

    def setOutput(self, output):
        self.output = output
        return self
    
    def setOutputDev(self, output):
        self.output_dev = output
        return self

    def set_website(self, website):
        self.website = website
        return self
