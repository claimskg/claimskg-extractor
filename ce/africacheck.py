# -*- coding: utf-8 -*-
import pandas as pd
import urllib2
from bs4 import BeautifulSoup
import datetime
import dateparser
import copy
import Claim as claim_obj
import requests
from dateparser.search import search_dates
import json
import re


def get_all_claims(criteria):
	headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}


	#print criteria.maxClaims
	#performing a search by each letter, and adding each article to a urls_ var.
	now = datetime.datetime.now()
	urls_={}
	types=["true","mostly-true","half-true","barely-true","false","pants-fire","no-flip","half-flip","full-flop"]
	last_page=[]
	for page_number in range (1,500):
		if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
			break

		url="https://africacheck.org/latest-reports/page/"+str(page_number)+"/"
		#url="http://www.politifact.com/truth-o-meter/rulings/"+str(type_)+"/?page="+str(page_number)
		try:
			page = requests.get(url, headers=headers, timeout=5)
			soup = BeautifulSoup(page.text,"lxml")
			soup.prettify()
			links = soup.findAll("div",{"class":"article-content"})
			if (len(links) != 0) or (links != last_page):
				for anchor in links:
					anchor = anchor.find('a', href=True)
					ind_=str(anchor['href'])
					if (ind_ not in urls_.keys()):
						if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
							break
						if (ind_ not in criteria.avoid_url):	
							urls_[ind_]=ind_
							print "adding "+str(ind_)
				last_page  = links
			else:
				print ("break!")
				break
		except:
				print "error=>"+str(url)

	claims=[]
	index=0
	# visiting each article's dictionary and extract the content.
	for url, conclusion in urls_.iteritems():  
		print str(index) + "/"+ str(len(urls_.keys()))+ " extracting "+str(url)
		index+=1

		url_complete=str(url)

		#print url_complete
		#try: 
		page = requests.get(url_complete, headers=headers, timeout=5)
		soup = BeautifulSoup(page.text,"lxml")
		soup.prettify("utf-8")

		claim_ =  claim_obj.Claim()
		claim_.setUrl(url_complete)
		claim_.setSource("africacheck")

		if (criteria.html):
			claim_.setHtml(soup.prettify("utf-8"))

		
		#title
		#if (soup.find("h1",{"class":"content-head__title"}) and len(soup.find("h1",{"class":"content-head__title"}).get_text().split("?"))>1):
		title=soup.find("meta",{"property":"og:title"})
		claim_.setTitle(title['content'])

		#date

		date_ = soup.find('time')
		#print date_["content"]
		if date_ : 
			date_str=search_dates(date_['datetime'].split(" ")[0])[0][1].strftime("%Y-%m-%d")
			#print date_str
			claim_.setDate(date_str)
			#print claim_.date


		#rating

		conclusion_=""
		if (soup.find("div",{"class":"verdict-stamp"})):
			conclusion_=soup.find("div",{"class":"verdict-stamp"}).get_text()
		if (soup.find("div",{"class":"verdict"})):
			conclusion_=soup.find("div",{"class":"verdict"}).get_text()
		if (soup.find("div",{"class":"indicator"})):
			conclusion_=soup.find("div",{"class":"indicator"}).get_text()
			if (soup.find("div",{"class":"indicator"}).find('span')):
				conclusion_=soup.find("div",{"class":"indicator"}).find('span').get_text()

		claim_.setAlternateName(str(re.sub('[^A-Za-z0-9\ -]+', '', conclusion_)).lower().strip() )
		
		#when there is no json
		
		date_=soup.find("time",{"class":"datetime"})
		if (date_):
			claim_.setDate(date_.get_text())

				
		#print claim_.alternateName 
		#body
		body=soup.find("div",{"id":"main"})
		claim_.setBody(body.get_text())

		#author
		author=soup.find("div",{"class":"sharethefacts-speaker-name"})
		if (author ):
			claim_.setAuthor(author.get_text())



		#related links
		divTag = soup.find("div",{"id":"main"})
		related_links=[]
		for link in divTag.findAll('a', href=True):
		    related_links.append(link['href'])
		claim_.setRefered_links(related_links)
		

		if (soup.find("div",{"class":"report-claim"})):
			claim_.setClaim(soup.find("div",{"class":"report-claim"}).find("strong").get_text())
		else:
			claim_.setClaim(claim_.title)
		

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