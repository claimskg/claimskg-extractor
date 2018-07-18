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
				ind_ = anchor['href']
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
			page = urllib2.urlopen(url_complete).read().decode('utf-8', 'ignore')
			soup = BeautifulSoup(page, "lxml")
			soup.prettify("utf-8")

			claim_ =  claim_obj.Claim()
			claim_.setUrl(url_complete)
			claim_.setSource("snopes")

			if (criteria.html):
				claim_.setHtml(soup.prettify("utf-8"))

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


			#author
			author=soup.find("span",{"itemprop":"itemReviewed"})
			if (author and author.find("span",{"itemprop":"author"})):
				claim_.setAuthor(author.find("span",{"itemprop":"author"}).find("meta",{"itemprop":"name"})['content'])

			#sameas
			obj=soup.find("span",{"itemprop":"itemReviewed"})
			if (obj and obj.find("meta",{"itemprop":"sameAs"})):
				claim_.setSameAs(obj.find("meta",{"itemprop":"sameAs"})['content'])
				

			#samdatepublished
			obj=soup.find("span",{"itemprop":"itemReviewed"})
			if (obj and obj.find("meta",{"itemprop":"datePublished"})):
				date_=obj.find("meta",{"itemprop":"datePublished"})['content']
				if (date_.split("T")>1):
					claim_.setDatePublished(date_.split("T")[0])


			#rating
			obj=soup.find("span",{"itemprop":"reviewRating"})
			if (obj):
				claim_.ratingValue= obj.find("meta",{"itemprop":"ratingValue"})['content']
				claim_.worstRating= obj.find("meta",{"itemprop":"worstRating"})['content']
				claim_.bestRating= obj.find("meta",{"itemprop":"bestRating"})['content']
				claim_.alternateName= obj.find("span",{"itemprop":"alternateName"}).text


			#related links
			divTag = soup.find("div",{"class":"article-text-inner"})
			related_links=[]
			for link in divTag.findAll('a', href=True):
			    related_links.append(link['href'])
			claim_.setRefered_links(related_links)
			


			claim_.setClaim(soup.find('meta', {"itemprop": "claimReviewed"})["content"])
			#claim_.setConclusion(soup.find('span', {"itemprop": "alternateName"}).text)

			tags=[]

			for tag in soup.findAll('meta', {"property":"article:tag"}):
				#print "achou"
				tags.append(tag["content"])
			claim_.setTags(", ".join(tags))

			claims.append(claim_.getDict())
		except:
			print "Error ->" + str(url_complete)

    #creating a pandas dataframe
	pdf=pd.DataFrame(claims)
	return pdf