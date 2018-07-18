class Claim:

	def __init__(self):
		self.source=""
		self.claim=unicode("")
		self.body=unicode("")
		self.conclusion=unicode("")
		self.refered_links=""
		self.title=unicode("")
		self.date=""
		self.url=""
		self.tags=""
		self.author=""
		self.datePublished=""
		self.sameAs=""
		self.source_url=""
		self.html=False
		self.ratingValue="-1"
		self.worstRating="-1"
		self.bestRating="-1"
		self.alternateName=""


	def setRatingValue(self, str_):
		if str_:
			str_=str(str_).replace('"',"")
			self.ratingValue = str_
		return self

	def setWorstRating(self, str_):
		if str_:
			str_=str(str_).replace('"',"")
			self.worstRating = str_
		return self

	def setBestRating(self, str_):
		if str_:
			str_=str(str_).replace('"',"")
			self.bestRating = str_
		return self

	def setAlternateName(self, str_):
		str_=str(str_).replace('"',"")
		#split sentence
		if (str_.split(".")>0):
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

	def setConclusion(self, str_):
		#old! just to be sure that new websites export the same informatio
		self.conclusion = unicode(str_)
		self.alternateName = self.conclusion
		return self

	def setRefered_links(self, str_):
		self.refered_links = str_
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
		dict_={}
		#class rating
		dict_['rating_ratingValue']=self.ratingValue
		dict_['rating_worstRating']=self.worstRating
		dict_['rating_bestRating']=self.bestRating
		dict_['rating_alternateName']=self.alternateName

		#class creative work
		dict_['creativeWork_author_name']=self.author
		dict_['creativeWork_datePublished']=self.datePublished
		dict_['creativeWork_author_sameAs']=self.sameAs


		#class claimreview
		dict_['claimReview_author_name']=self.source
		dict_['claimReview_author_url']=self.source_url
		dict_['claimReview_url']=self.url
		dict_['claimReview_claimReviewed']=self.claim
		dict_['claimReview_datePublished']=self.date


		#extra information
		dict_['extra_body']=self.body.replace("\n","")
		#dict_['conclusion']=self.conclusion
		dict_['extra_refered_links']=self.refered_links
		dict_['extra_title']=self.title
		dict_['extra_tags']=self.tags
		if (self.html):
			dict_['extra_html']=self.html
		return dict_

	def getOldDict(self):
		dict_={}
		dict_['author']=self.author
		dict_['datePublished']=self.datePublished
		dict_['sameAs']=self.sameAs
		dict_['source']=self.source
		dict_['claim']=self.claim
		dict_['body']=self.body.replace("\n","")
		dict_['conclusion']=self.conclusion
		dict_['refered_links']=self.refered_links
		dict_['title']=self.title
		dict_['date']=self.date
		dict_['url']=self.url
		dict_['tags']=self.tags
		if (self.html):
			dict_['html']=self.html
		return dict_
