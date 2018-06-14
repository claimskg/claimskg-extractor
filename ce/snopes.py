# -*- coding: utf-8 -*-
import pandas as pd
import urllib2
from bs4 import BeautifulSoup
import datetime
import dateparser
import copy
import Claim as claim_obj


def get_all_claims(criteria):
	print criteria.maxClaims
	#performing a search by each letter, and adding each article to a urls_ var.
	now = datetime.datetime.now()
	urls_={}
	for page_number in range (1,500):
		if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
			break
		try:
			page = urllib2.urlopen("https://www.snopes.com/fact-check/page/"+str(page_number)+"/").read()
		except:
			break
		soup = BeautifulSoup(page,"lxml")
		soup.prettify()
		links = soup.findAll('a',{"class":"article-link"}, href=True)
		if len(links) != 0:
			for anchor in links:
				if (anchor['href'] not in urls_.keys()):
					if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
						break
					urls_[anchor['href']]=page_number
					print "adding "+str(anchor['href'])
		else:
			print ("break!")
			break

	claims=[]
	index=0
	# visiting each article's dictionary and extract the content.
	for url, conclusion in urls_.iteritems():  
		print str(index) + "/"+ str(len(urls_.keys()))+ " extracting "+str(url)
		index+=1

		url_complete=str(url)

		#print url_complete
		page = urllib2.urlopen(url_complete).read().decode('utf-8', 'ignore')
		soup = BeautifulSoup(page, "lxml")
		soup.prettify("utf-8")

		claim_ =  claim_obj.Claim()
		claim_.setUrl(url_complete)
		claim_.setSource("snopes")

		if (criteria.html):
			claim_.setHtml(soup.prettify("utf-8"))

		#try:
		#title
		#if (soup.find("h1",{"class":"content-head__title"}) and len(soup.find("h1",{"class":"content-head__title"}).get_text().split("?"))>1):
		title=soup.find("h1",{"class":"article-title"})
		claim_.setTitle(title.text)

		#date

		date_ = soup.find('meta', {"itemprop": "datePublished"})
		#print date_["content"]
		if date_ : 
			date_str=dateparser.parse(date_["content"].split("T")[0], settings={'DATE_ORDER': 'YMD'}).strftime("%Y-%m-%d")
			#print date_str
			claim_.setDate(date_str)
			#print claim_.date


		#body
		body=soup.find("div",{"class":"article-text-inner"})
		claim_.setBody(body.get_text())

		#related links
		divTag = soup.find("div",{"class":"article-text-inner"})
		related_links=[]
		for link in divTag.findAll('a', href=True):
		    related_links.append(link['href'])
		claim_.setRefered_links(related_links)
		


		claim_.setClaim(soup.find('meta', {"itemprop": "claimReviewed"})["content"])
		claim_.setConclusion(soup.find('span', {"itemprop": "alternateName"}).text)

		tags=[]

		for tag in soup.findAll('meta', {"property":"article:tag"}):
			#print "achou"
			tags.append(tag["content"])
		claim_.setTags(", ".join(tags))

		claims.append(claim_.getDict())
		#except:
		#	print "Error ->" + str(url_complete)

    #creating a pandas dataframe
	pdf=pd.DataFrame(claims)
	return pdf