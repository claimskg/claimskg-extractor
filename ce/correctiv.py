# -*- coding: utf-8 -*-
import pandas as pd
import urllib2
from bs4 import BeautifulSoup
import datetime
import dateparser
import copy
import Claim as claim_obj
from dateparser.search import search_dates



def get_all_claims(criteria):
	print criteria.maxClaims
	#performing a search by each letter, and adding each article to a urls_ var.
	now = datetime.datetime.now()
	urls_={}
	for page_number in range (1,500):
		if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
			break
		try:
			url = "https://correctiv.org/echtjetzt/artikel/seite/"+str(page_number)+"/"
			page = urllib2.urlopen(url).read()
		except:
			break
		soup = BeautifulSoup(page,"lxml")
		soup.prettify()
		links = soup.findAll('a',{"class":"entry-list-item__link"}, href=True)
		if len(links) != 0:
			for anchor in links:
				url_to_add="https://correctiv.org"+str(anchor['href'])
				if (url_to_add not in urls_.keys()):
					if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
						break
					urls_[url_to_add]=page_number
					print "adding "+str(url_to_add)
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
		#try: 
		page = urllib2.urlopen(url_complete).read().decode('utf-8', 'ignore')
		soup = BeautifulSoup(page, "lxml")
		soup.prettify("utf-8")

		claim_ =  claim_obj.Claim()
		claim_.setUrl(url_complete)
		claim_.setSource("correctiv")

		if (criteria.html):
			claim_.setHtml(soup.prettify("utf-8"))

		#title
		#if (soup.find("h1",{"class":"content-head__title"}) and len(soup.find("h1",{"class":"content-head__title"}).get_text().split("?"))>1):
		title=soup.find("h1",{"class":"article-header__headline"})
		claim_.setTitle(title.text.replace("Faktencheck: ","").replace("\n",""))

		#date

		date_ = soup.find('time', {"class": "article-body__publishing-date"})
		#print date_["content"]
		if date_ : 
			date_str=search_dates(date_.text)[0][1].strftime("%Y-%m-%d")
			#print date_str
			claim_.setDate(date_str)
			#print claim_.date


		#body
		body=soup.find("div",{"class":"article-body__main"})
		claim_.setBody(body.get_text())

		#related links
		divTag = soup.find("div",{"class":"article-body__main"})
		related_links=[]
		for link in divTag.findAll('a', href=True):
		    related_links.append(link['href'])
		claim_.setRefered_links(related_links)
		


		claim_.setClaim(claim_.title)
		conclsion=soup.find('div', {"class": "article-body__claimreview claimreview"})
		if conclsion:
			claim_.setConclusion(conclsion.text.replace("Unsere Bewertung: ","").replace("\n",""))


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