import pandas as pd
import spacy
import json
import spotlight
import cgi
import export_rdf as e_rdf

count_=0
current_websites={
	"english":["snopes","politifact","truthorfiction","checkyourfact","factscan","africacheck"],
	"portuguese":["aosfatos","lupa","publica","g1","efarsas"],
	"german":["mimikama","correctiv"] 
}

current_websites_invert = {}
for key in current_websites.keys():
	for web_ in current_websites[key]:
		current_websites_invert[web_]=key

spacy_portuguese = None
spacy_english = None
spacy_germam = None

def get_sites():
	print current_sites


def get_claims(criteria):

	def delete_unamed_col(pdf):
		un_col=[]
		index_=-1
		for c in pdf.columns:
			index_+=1
			#print str(c)
			if "Unnamed:" in c:
				#print "drop"+c
				un_col.append(index_)
		
		pdf=pdf.drop(pdf.columns[un_col], axis=1)
		return pdf

	if (criteria.update_db):
		#print "passou aqui"
		#print criteria.input
		pdf_old=pd.read_csv(criteria.input, encoding="utf8")
		criteria.avoid_url = pdf_old['claimReview_url'].values

		criteria.output = criteria.input
		if (criteria.website and criteria.website.split(",")>1):
			pdfs=[]
			for web in criteria.website.split(","):
				module = __import__(web)
				func = getattr(module, "get_all_claims")
				pdfs.append( func(criteria))
			pdf_new = pd.concat(pdfs)
			pdf_new = delete_unamed_col(pdf_new)
			pdf_old = delete_unamed_col(pdf_old)
			pdf = pd.concat([pdf_old,pdf_new], ignore_index=True)
			pdf = delete_unamed_col(pdf)

		elif (criteria.language):
			pdfs=[]
			for website in current_websites[criteria.language]:
				module = __import__(website)
				func = getattr(module, "get_all_claims")
				pdfs.append( func(criteria))
			pdf_new = pd.concat(pdfs)
			pdf_new = delete_unamed_col(pdf_new)
			pdf_old = delete_unamed_col(pdf_old)
			pdf = pd.concat([pdf_old,pdf_new], ignore_index=True)
			pdf = delete_unamed_col(pdf)

		# else:
		# 	module = __import__(criteria.website)
		# 	func = getattr(module, "get_all_claims")
		# 	pdf_new=func(criteria)
		# 	pdf = pdf_new.append(pdf_old)

	elif (criteria.website):
		if (criteria.website.split(",")>1):
			pdfs=[]
			for web in criteria.website.split(","):
				module = __import__(web)
				func = getattr(module, "get_all_claims")
				pdfs.append( func(criteria))
			pdf = pd.concat(pdfs)
		else:
			module = __import__(criteria.website)
			func = getattr(module, "get_all_claims")
			pdf = func(criteria)
		#pdf.to_csv(criteria.output, encoding="utf8")

	elif (criteria.input):
		pdf=pd.read_csv(criteria.input, encoding="utf8")

	else:
		pdfs=[]
		language  = criteria.language
		for website in current_websites[language]:
			module = __import__(website)
			func = getattr(module, "get_all_claims")
			pdfs.append( func(criteria))
		pdf = pd.concat(pdfs)
	#pdf['claimReview_datePublished'] = pd.to_datetime(pdf['claimReview_datePublished'], format='%Y-%m-%d')


	#if (criteria.maxClaims>0):
	#	pdf = pdf[:criteria.maxClaims]



		#pdf = pdf[pdf['claimReview_datePublished']>=criteria.since]


	if (criteria.since):
		pdf = pdf[pdf['claimReview_datePublished']>=criteria.since]

	if (criteria.until):
		pdf = pdf[pdf['claimReview_datePublished']<=criteria.until]

	if (criteria.entity):
		print "Extracting Entities..."
		pdf = extract_entities_from_pdf(pdf)


	if (criteria.entity_link):
		print "Extracting Entities link..."
		pdf = extract_entities_link_from_pdf(pdf)

	if (criteria.rdf):
		#pdf = extract_entities_link_from_pdf(pdf)
		#criteria.entity_link=None
		#criteria.entity=None
		out=e_rdf.export_rdf(pdf,criteria)
		file = open(str(criteria.output)+"."+str(criteria.rdf), "w")
		file.write(out)

	pdf.to_csv(criteria.output, encoding="utf-8")


def extract_entities_link_from_pdf(pdf):
	global count_
	count_=len(pdf)
	pdf["extra_entities_claimReview_claimReviewed"] = pdf.apply(lambda x: get_entities_link(x['claimReview_claimReviewed'],current_websites_invert[x['claimReview_author_name']]),axis=1)
	count_=len(pdf)
	pdf["extra_entities_body"] = pdf.apply(lambda x: get_entities_link(x['extra_body'],current_websites_invert[x['claimReview_author_name']]),axis=1)

	def extract_json_entities_link(pdf,col):
		data_=[]
		for index, row in pdf.iterrows(): 
		    row_={}
		    json_=json.loads(row[col])
		    
		    for i in json_:
		        #print type(i)
		        #print i.keys()
		        if i[u'types']:
		            for class_ in i[u'types'].split(","):
		                if ("DBpedia:" in class_):
		                    if class_ in row_.keys():
		                        row_[class_].append(json.dumps(i))
		                    else:
		                        row_[class_]=[json.dumps(i)]
		    data_.append(row_)


		pdf =  pd.DataFrame(data_)
		for c in pdf.columns.values:
		    pdf.rename(columns = {c:str(col)+"_"+str(c)}, inplace = True)
		return pdf

	# entities_claim =extract_json_entities_link(pdf,'extra_entities_claimReview_claimReviewed')
	# entities_body =extract_json_entities_link(pdf,'extra_entities_body')

	# pdf = pd.concat([pdf,entities_claim,entities_body],axis=1)	
	return pdf


def get_entities_link(str_,language):
	global count_
	count_-=1
	print count_
	annotations= []
	#to solve float errors 
	if (type(str_)==type(1.0)):
		str_=""
	else:
		str_=cgi.escape(str_).encode('ascii', 'xmlcharrefreplace')
	try:
		if language == "english":
			annotations = spotlight.annotate('http://model.dbpedia-spotlight.org/en/annotate',str_, confidence=0.4, support=20)
		elif language == "german":
			annotations = spotlight.annotate('http://api.dbpedia-spotlight.org/de/annotate',str_, confidence=0.4, support=20)
		elif language == "portuguese":
			annotations = spotlight.annotate('http://api.dbpedia-spotlight.org/pt/annotate',str_, confidence=0.4, support=20)
	except:
		annotations= []
		#print "error claim= " + str_

	return json.dumps(annotations)


def extract_entities_from_pdf(pdf):
	pdf["extra_entities_claimReview_claimReviewed"] = pdf.apply(lambda x: get_entities(x['claimReview_claimReviewed'],current_websites_invert[x['claimReview_author_name']]),axis=1)
	pdf["extra_entities_body"] = pdf.apply(lambda x: get_entities(x['extra_body'],current_websites_invert[x['claimReview_author_name']]),axis=1)

	return pdf

def get_entities(str_,language):
	global spacy_portuguese
	global spacy_english
	global spacy_germam


	if language == "english":
		if (spacy_english == None):
			spacy_english = spacy.load('en')
		nlp = spacy_english
	elif language == "german":
		if (spacy_germam == None):
			spacy_germam = spacy.load('de')
		nlp = spacy_germam
	elif language == "portuguese":
		if (spacy_portuguese == None):
			spacy_portuguese = spacy.load('pt')
		nlp = spacy_portuguese
	doc = nlp(unicode(str_))

	labels={}
	for x in doc.ents:
		if x.label_ in labels.keys():
			labels[x.label_].append(x.text)
		else:
			labels[x.label_]=[x.text]		
	#print labels
	return json.dumps(labels)
