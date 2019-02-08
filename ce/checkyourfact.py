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

	urls_={}
	for page_number in range (1,500):
		if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
			break
		try:
			url = "https://checkyourfact.com/page/"+str(page_number)+"/"
			page = requests.get(url, headers=headers, timeout=10)
			soup = BeautifulSoup(page.text,"lxml")
			soup.prettify()
		except:
			break
		links = soup.find('articles').findAll('a', href=True)
		if len(links) != 0:
			for anchor in links:
				ind_="http://checkyourfact.com"+str(anchor['href'])
				if (ind_ not in urls_.keys()):
					if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
						break
					if (ind_ not in criteria.avoid_url):
						urls_[ind_]=page_number
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
		try: 
			page = requests.get(url_complete, headers=headers, timeout=5)
			soup = BeautifulSoup(page.text,"lxml")
			soup.prettify("utf-8")

			claim_ =  claim_obj.Claim()
			claim_.setUrl(url_complete)
			claim_.setSource("checkyourfact")

			if (criteria.html):
				claim_.setHtml(soup.prettify("utf-8"))

			#title
			title=soup.find('article').find("h1")
			claim_.setTitle(title.text.replace("FACT CHECK: ",""))



			date_str=search_dates(url_complete.replace("http://dailycaller.com/", "").replace("/"," ") , settings={'DATE_ORDER': 'YMD'})[0][1].strftime("%Y-%m-%d")
			#print date_str
			claim_.setDate(date_str)
			#print claim_.date


			#body
			body=soup.find("article")
			claim_.setBody(body.get_text())

			#related links
			divTag = soup.find("article")
			related_links=[]
			for link in divTag.findAll('a', href=True):
			    related_links.append(link['href'])
			claim_.setRefered_links(related_links)
			


			claim_.setClaim(claim_.title)

			for strong in soup.find('article').findAll('strong'):
				if "Verdict:" in strong.text:
					claim_.setConclusion(strong.text.replace("Verdict: ",""))


			tags=[]

			for tag in soup.findAll('meta', {"property":"article:tag"}):
				#print "achou"
				tags.append(tag["content"])
			claim_.setTags(", ".join(tags))

			claims.append(claim_.generate_dictionary())
		except:
			print "Error ->" + str(url_complete)

    #creating a pandas dataframe
	pdf=pd.DataFrame(claims)
	return pdf