import pandas as pd
import spacy
import json
import spotlight
import cgi
import export_rdf as e_rdf
import urllib,urllib2,xml
import lxml
from lxml.html.clean import Cleaner

cleaner = Cleaner()
cleaner.javascript = True # This is True because we want to activate the javascript filter
cleaner.style = True      # This is True because we want to activate the styles & stylesheet filter
cleaner.page_structure=True


## dictiony used to normalize lternateName filed 
dict_normalized_alternateName={

"africacheck-incorrect":"FALSE",
"africacheck-mostly-correct":"MIXTURE",
"africacheck-correct":"TRUE",

"factscan-false":"FALSE",
"factscan-true":"TRUE",

"checkyourfact-false":"FALSE",
"checkyourfact-true":"TRUE",
"checkyourfact-mostly true":"MIXTURE",
"checkyourfact-true/false":"MIXTURE",

"snopes-false":"FALSE",
"snopes-mixture":"MIXTURE",
"snopes-true":"TRUE",
"snopes-mostly false":"MIXTURE",
"snopes-mostly true":"MIXTURE",
"snopes-correct attribution":"TRUE",
"snopes-scan":"FALSE",

"politifact-pants-fire":"FALSE",
"politifact-pants on fire":"FALSE",
"politifact-false":"FALSE",
"politifact-mostly false":"MIXTURE",
"politifact-barely true":"MIXTURE",
"politifact-half true":"MIXTURE",
"politifact-mostly true":"MIXTURE",
"politifact-true":"TRUE",

"truthorfiction-fiction":"FALSE",
"truthorfiction-truth":"TRUE",
"truthorfiction-truth & fiction":"MIXED",
"truthorfiction-mostly fiction":"MIXED",
"truthorfiction-truth & misleading":"MIXED",
"truthorfiction-reported as fiction":"FALSE",
"truthorfiction-mostly truth":"MIXED",
"truthorfiction-farcical":"FALSE",
}
default_label="OTHER"



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

	# if (criteria.entity):
	# 	print "Extracting Entities..."
	# 	pdf = extract_entities_from_pdf(pdf)

	if (criteria.normalize_credibility):
		print "Normalizing labels..."
		pdf = normalize_credibility(pdf)

	if (criteria.entity_link):
		print "Extracting Entities..."
		#pdf = parallelize_dataframe(pdf, extract_entities_link_from_pdf)
		pdf = extract_entities_link_from_pdf(pdf)

	if (criteria.rdf):
		#pdf = extract_entities_link_from_pdf(pdf)
		#criteria.entity_link=None
		#criteria.entity=None
		out=e_rdf.export_rdf(pdf,criteria)
		file = open(str(criteria.output)+"."+str(criteria.rdf), "w")
		file.write(out)

	pdf.to_csv(criteria.output, encoding="utf-8")



def get_normalized_alternateName(site,label):
	key_=site+"-"+str(label).lower()
	if key_ in dict_normalized_alternateName.keys():
		return dict_normalized_alternateName[key_]
	else:
		return default_label

def normalize_credibility(pdf):
	pdf["rating_alternateName_normalized"] = pdf.apply(lambda x: get_normalized_alternateName(x['claimReview_author_name'],x['rating_alternateName']),axis=1)
	return pdf



def extract_entities_link_from_pdf(pdf):
	count_=0
	pdf["extra_entities_claimReview_claimReviewed"] = pdf.apply(lambda x: get_entities_link(x['claimReview_claimReviewed'],current_websites_invert[x['claimReview_author_name']]),axis=1)
	count_=0
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
	import requests
	import subprocess
	#print "passou aqui"
	global count_
	count_+=1
	print count_
	annotations= []
	#to solve float errors 
	if (type(str_)==type(1.0)):
		str_=""
	else:
		import re
		#str_=cgi.escape(str_).encode('ascii', 'xmlcharrefreplace')
		#remove html from string 
		#
		str_= cleaner.clean_html(str_)
		str_=urllib.quote_plus(cgi.escape(str_).encode('ascii', 'xmlcharrefreplace'))
		#print len (str_)
		#if len (str_)  > 2000:
		#	print str_
		
	try:
		if language == "english":
			#annotations = spotlight.annotate('http://model.dbpedia-spotlight.org/en/annotate',str_, confidence=0.4, support=20)
			# url="http://localhost:8080/dexter-webapp/api/rest/annotate?min-conf=0.4&text="+str_
			# contents  = urllib2.urlopen(url).read()
			# data = json.loads(contents)

			url = 'http://localhost:8080/dexter-webapp/api/rest/annotate'
			params = {'min-conf': '0.4','text': str_}
			response = requests.post(url, data=params)
			data =json.loads(response.text)
			#print data['spots']
			annotations = data['spots']


		elif language == "german":
			annotations = spotlight.annotate('http://api.dbpedia-spotlight.org/de/annotate',str_, confidence=0.4, support=20)
		elif language == "portuguese":
			annotations = spotlight.annotate('http://api.dbpedia-spotlight.org/pt/annotate',str_, confidence=0.4, support=20)
	except:
		annotations= []
		print "error trying to annotate text= " 
	#print "passou aqui 3"
	#print json.dumps(annotations)
	return json.dumps(annotations)


# def extract_entities_from_pdf(pdf):
# 	pdf["extra_entities_claimReview_claimReviewed"] = pdf.apply(lambda x: get_entities(x['claimReview_claimReviewed'],current_websites_invert[x['claimReview_author_name']]),axis=1)
# 	pdf["extra_entities_body"] = pdf.apply(lambda x: get_entities(x['extra_body'],current_websites_invert[x['claimReview_author_name']]),axis=1)

# 	return pdf

# def get_entities(str_,language):
# 	global spacy_portuguese
# 	global spacy_english
# 	global spacy_germam


# 	if language == "english":
# 		if (spacy_english == None):
# 			spacy_english = spacy.load('en')
# 		nlp = spacy_english
# 	elif language == "german":
# 		if (spacy_germam == None):
# 			spacy_germam = spacy.load('de')
# 		nlp = spacy_germam
# 	elif language == "portuguese":
# 		if (spacy_portuguese == None):
# 			spacy_portuguese = spacy.load('pt')
# 		nlp = spacy_portuguese
# 	doc = nlp(unicode(str_))

# 	labels={}
# 	for x in doc.ents:
# 		if x.label_ in labels.keys():
# 			labels[x.label_].append(x.text)
# 		else:
# 			labels[x.label_]=[x.text]		
# 	#print labels
# 	return json.dumps(labels)


# import multiprocessing
# import pandas as pd
# import numpy as np

# #from gevent.pool import Pool
# from multiprocessing import Pool

# num_partitions = 4
# num_cores = multiprocessing.cpu_count()
 
# # def parallelize_dataframe(df, func):
# #     a,b,c,d,e = np.array_split(df, num_partitions)
# #     print a
# #     pool = Pool(num_cores)
# #     df = pd.concat(pool.map(func, [a,b,c,d,e]))
# #     pool.close()
# #     pool.join()
# #     return df

# def parallelize_dataframe(df, func):
#     df_split = np.array_split(df, num_partitions)
#     pool = Pool(num_cores)
#     #print df_split
#     df = pd.concat(pool.map(func, df_split))
#     pool.close()
#     pool.join()
#     return df

