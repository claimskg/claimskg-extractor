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
		url="http://factscan.ca/page/"+str(page_number)+"/"
		#url="http://www.politifact.com/truth-o-meter/rulings/"+str(type_)+"/?page="+str(page_number)
		try:
			page = requests.get(url, headers=headers, timeout=5)
			soup = BeautifulSoup(page.text,"lxml")
			soup.prettify()
			links = soup.findAll("h1",{"class":"post-title entry-title home-feed-title"})
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
		try: 
			page = requests.get(url_complete, headers=headers, timeout=5)
			soup = BeautifulSoup(page.text,"lxml")
			soup.prettify("utf-8")

			claim_ =  claim_obj.Claim()
			claim_.setUrl(url_complete)
			claim_.setSource("factscan")

			if (criteria.html):
				claim_.setHtml(soup.prettify("utf-8"))

			#print url_complete
			#import ast
			json_ = None
			if (soup.find("script",{"type":"application/ld+json"})):
				json_=soup.find("script",{"type":"application/ld+json"}).get_text()

			def parse_wrong_json(json_,left,right):
				if json_:
					if (len(json_.split(left))>0):
						return json_.split(left)[1].split(right)[0]
				else:
					return None


			#title
			#if (soup.find("h1",{"class":"content-head__title"}) and len(soup.find("h1",{"class":"content-head__title"}).get_text().split("?"))>1):
			title=soup.find("meta",{"property":"og:title"})['content']
			claim_.setTitle(title)

			#date

			date_ = soup.find('meta', {"property": "article:published_time"})
			#print date_["content"]
			if date_ : 
				date_str=search_dates(date_['content'].split("T")[0])[0][1].strftime("%Y-%m-%d")
				#print date_str
				claim_.setDate(date_str)
				#print claim_.date


			#rating

			claim_.set_rating_value(parse_wrong_json(json_, '"ratingValue":', ","))
			claim_.setWorstRating(parse_wrong_json(json_,'"worstRating":',","))
			claim_.setBestRating(parse_wrong_json(json_,'"bestRating":',","))
			claim_.setAlternateName(parse_wrong_json(json_,'"alternateName":',","))
			
			#when there is no json
			if (claim_.alternateName==None) :
				#print "não achou conclusao"
				if (soup.find("div",{"class":"fact-check-icon"})):
					#print "passou"
					if (soup.find("div",{"class":"fact-check-icon"}).find('img')):
						#print "passou2"
						claim_str=soup.find("div",{"class":"fact-check-icon"}).find('img')['alt'].split(":")[1]
						#print claim_str
						claim_.alternateName = claim_str
			#print claim_.alternateName 
			#body
			body=soup.find("div",{"class":"entry-content"})
			claim_.setBody(body.get_text())

			#author
			author=soup.find("div",{"class":"sharethefacts-speaker-name"})
			if (author ):
				claim_.setAuthor(author.get_text())



			#sameas
			claim_.setSameAs(parse_wrong_json(json_,'"sameAs": [',"]"))

			
			#obj=soup.find("div",{"itemprop":"itemReviewed"})
			#if (obj and obj.find("div",{"itemprop":"datePublished"})):
			#print parse_wrong_json(json_,'"}, "datePublished":',",")
			 
			#claim_.setDatePublished()


			#related links
			divTag = soup.find("div",{"class":"entry-content"})
			related_links=[]
			for link in divTag.findAll('a', href=True):
			    related_links.append(link['href'])
			claim_.setRefered_links(related_links)
			

			if (soup.find("div",{"class":"sharethefacts-statement"})):
				claim_.setClaim(soup.find("div",{"class":"sharethefacts-statement"}).get_text())
			else:
				claim_.setClaim(claim_.title)

			claim_.setConclusion(soup.find("div",{"class":"fact-check-icon-loop"}).find('img')['alt'].replace("FactsCan Score: ",""))
			
			

			tags=[]

			for tag in soup.findAll('meta', {"property":"article:tag"}):
				#print "achou"
				tags.append(tag["content"])
			claim_.setTags(", ".join(tags))


			if (claim_.conclusion.replace(" ","")=="" or claim_.claim.replace(" ","")==""):
				#print " eroor conclusion or claim"
				#print claim_.claim
				#print claim_.conclusion 
				raise ValueError('No conclusion or claim')

			claims.append(claim_.generate_dictionary())
		except:
			print "Error ->" + str(url_complete)

    #creating a pandas dataframe
	pdf=pd.DataFrame(claims)
	return pdf