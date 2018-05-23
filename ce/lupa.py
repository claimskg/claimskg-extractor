import pandas as pd
import urllib2
from bs4 import BeautifulSoup
import datetime
import re
import dateparser
import Claim as claim_obj

def get_all_claims(criteria):
	#performing a search by each letter, and adding each article to a urls_ var.
	now = datetime.datetime.now()
	urls_={}
	for year in range (2015,now.year+1):
		for month in range (1,13):
			if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
				break
			try:
				page = urllib2.urlopen("http://piaui.folha.uol.com.br/lupa/"+str(year)+"/"+str(month)+"/").read()
			except:
				break
			soup = BeautifulSoup(page,"lxml")
			soup.prettify()
			links = soup.find('div', {"class": "lista-noticias"}).findAll('a', href=True)
			if len(links) != 0:
				for anchor in links:
					if (anchor['href'] not in urls_.keys()):
						urls_[anchor['href']]=[year,month]
						print "adding "+str(anchor['href'])
						if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
							break
			else:
			    print ("break!")
			    break

	claims=[]
	index=0
	# visiting each article's dictionary and extract the content.
	for url in urls_.keys():
		print str(index) + "/"+ str(len(urls_.keys()))+ " extracting "+str(url)
		index+=1
		claim_ =  claim_obj.Claim()
		claim_.setSource("lupa")
		url_complete=url
		claim_.setUrl(url_complete)
		page = urllib2.urlopen(url_complete).read()
		soup = BeautifulSoup(page,"lxml")
		soup.prettify()
		

		#conclusin
		conclusion=soup.find('div', {"class": "etiqueta"})
		if conclusion :
			claim_.setConclusion(conclusion.get_text())
		    
		#title
		title=soup.find("h2", {"class": "bloco-title"})
		claim_.setTitle(title.text)


		#claim
		claim = soup.find('div', {"class": "post-inner"}).find('div', {"class": "etiqueta"})
		if claim and claim.find_previous('strong'):
			claim_.setClaim(claim.find_previous('strong').get_text())
		else:
			claim_.setClaim(claim_.title)

		#date
		date=soup.find("div", {"class": "bloco-meta"})
		claim_.setDate(dateparser.parse(date.text.split("|")[0]).strftime("%Y-%m-%d"))

		#related links
		divTag = soup.find("div", {"class": "post-inner"})
		related_links=[]
		for link in divTag.findAll('a', href=True):
		    related_links.append(link['href'])
		claim_.setRefered_links(related_links)

		#related links
		body = soup.find("div", {"class": "post-inner"})
		claim_.setBody(body.get_text())

		claims.append(claim_.getDict())
    
    #creating a pandas dataframe
	pdf=pd.DataFrame(claims)
	return pdf