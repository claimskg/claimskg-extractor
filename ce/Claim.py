class Claim:

    def __init__(self):
        self.source = ""
        self.claim = unicode("")
        self.body = unicode("")
        self.referred_links = ""
        self.title = unicode("")
        self.date = ""
        self.url = ""
        self.tags = ""
        self.author = ""
        self.datePublished = ""
        self.sameAs = ""
        self.source_url = ""
        self.html = False
        self.ratingValue = ""
        self.worstRating = ""
        self.bestRating = ""
        self.alternateName = ""

    def set_rating_value(self, string_value):
        if string_value:
            string_value = str(string_value).replace('"', "")
            self.ratingValue = string_value
        return self

    def setWorstRating(self, str_):
        if str_:
            str_ = str(str_).replace('"', "")
            self.worstRating = str_
        return self

    def setBestRating(self, str_):
        if str_:
            str_ = str(str_).replace('"', "")
            self.bestRating = str_
        return self

    def setAlternateName(self, str_):
        str_ = str(str_).replace('"', "")
        # split sentence
        if (str_.split(".") > 0):
            self.alternateName = str_.split(".")[0]
        else:
            self.alternateName = str_
        return self

    def setSource(self, str_):
        self.source = str_
        return self

    def setAuthor(self, str_):
        self.author = str_
        return self

    def setSameAs(self, str_):
        self.sameAs = str_
        return self

    def setDatePublished(self, str_):
        self.datePublished = str_
        return self

    def setClaim(self, str_):
        self.claim = unicode(str_)
        return self

    def setBody(self, str_):
        self.body = unicode(str_)
        return self

    def setRefered_links(self, str_):
        self.referred_links = str_
        return self

    def setTitle(self, str_):
        self.title = unicode(str_)
        return self

    def setDate(self, str_):
        self.date = str_
        return self

    def setUrl(self, str_):
        self.url = unicode(str_)
        return self

    def setTags(self, str_):
        self.tags = str_

    def setHtml(self, str_):
        self.html = str_

    def getDict(self):
        dict_ = {'rating_ratingValue': self.ratingValue, 'rating_worstRating': self.worstRating,
                 'rating_bestRating': self.bestRating, 'rating_alternateName': self.alternateName,
                 'creativeWork_author_name': self.author, 'creativeWork_datePublished': self.datePublished,
                 'creativeWork_author_sameAs': self.sameAs, 'claimReview_author_name': self.source,
                 'claimReview_author_url': self.source_url, 'claimReview_url': self.url,
                 'claimReview_claimReviewed': self.claim, 'claimReview_datePublished': self.date,
                 'extra_body': self.body.replace("\n", ""), 'extra_refered_links': self.referred_links,
                 'extra_title': self.title, 'extra_tags': self.tags}
        if self.html:
            dict_['extra_html'] = self.html
        return dict_
