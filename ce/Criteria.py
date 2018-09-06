class Criteria:
	
	def __init__(self):
		self.maxClaims = 0
		self.within = "15mi"
		self.output = "output.csv"
		self.language = "english"
		self.website=""
		self.until=None
		self.since=None
		self.html=False
		self.entity=False
		self.input=None
		self.rdf=None
		self.avoid_url=[]
		self.update_db=False
		self.entity_link=False
		self.normalize_credibility=True

		
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

	def setLanguage(self, language):
		self.language = language
		return self

	def setWebsite(self, website):
		self.website = website
		return self

