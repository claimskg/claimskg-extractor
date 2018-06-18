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


def get_all_claims(criteria):
	headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}


	#print criteria.maxClaims
	#performing a search by each letter, and adding each article to a urls_ var.
	now = datetime.datetime.now()
	urls_={}
	types=["true","mostly-true","half-true","barely-true","false","pants-fire","no-flip","half-flip","full-flop"]
	for type_ in types:
		for page_number in range (1,500):
			if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
				break
			#try:

			url="http://www.politifact.com/truth-o-meter/rulings/"+str(type_)+"/?page="+str(page_number)
			page = requests.get(url, headers=headers, timeout=5)
			soup = BeautifulSoup(page.text,"lxml")
			soup.prettify()

			links = soup.findAll("p",{"class":"statement__text"})
			if len(links) != 0:
				for anchor in links:
					anchor = anchor.find('a', {"class": "link"}, href=True)
					if (anchor['href'] not in urls_.keys()):
						if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
							break
						ind_="http://www.politifact.com"+str(anchor['href'])
						urls_[ind_]=type_
						print "adding "+str(ind_)
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
		page = requests.get(url_complete, headers=headers, timeout=5)
		soup = BeautifulSoup(page.text,"lxml")
		soup.prettify("utf-8")

		claim_ =  claim_obj.Claim()
		claim_.setUrl(url_complete)
		claim_.setSource("politifact")

		if (criteria.html):
			claim_.setHtml(soup.prettify("utf-8"))

		#title
		#if (soup.find("h1",{"class":"content-head__title"}) and len(soup.find("h1",{"class":"content-head__title"}).get_text().split("?"))>1):
		title=soup.find("h1",{"class":"article__title"})
		claim_.setTitle(title.text)

		#date

		date_ = soup.find('div', {"class": "widget__content"}).find("p") 
		#print date_["content"]
		if date_ : 
			date_str=search_dates(date_.text)[0][1].strftime("%Y-%m-%d")
			#print date_str
			claim_.setDate(date_str)
			#print claim_.date


		#body
		body=soup.find("div",{"class":"article__text"})
		claim_.setBody(body.get_text())

		#related links
		divTag = soup.find("div",{"class":"article__text"})
		related_links=[]
		for link in divTag.findAll('a', href=True):
		    related_links.append(link['href'])
		claim_.setRefered_links(related_links)
		


		claim_.setClaim(soup.find("h1",{"class":"article__title"}).text)
		claim_.setConclusion(conclusion)

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