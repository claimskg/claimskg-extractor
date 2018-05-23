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
	for type_ in ["verdadeiro","impreciso","exagerado","contraditorio","insustentavel","falso"]:
		for page_number in range (1,500):
			if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
				break
			try:
				page = urllib2.urlopen("http://aosfatos.org/noticias/checamos/"+str(type_)+"/?page="+str(page_number)).read()
			except:
				break
			soup = BeautifulSoup(page,"lxml")
			soup.prettify()
			links = soup.findAll('a',{"class":"card third"}, href=True)
			if len(links) != 0:
				for anchor in links:
					if (anchor['href'] not in urls_.keys()):
						if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
							break
						urls_[anchor['href']]=type_
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

		url_complete="https://aosfatos.org/"+str(url)

		#print url_complete
		page = urllib2.urlopen(url_complete).read()
		soup = BeautifulSoup(page, "lxml")
		soup.prettify()

		for claim_element in soup.findAll("blockquote"):
			claim_ =  claim_obj.Claim()
			claim_.setUrl(url_complete)
			claim_.setSource("aosfatos")


			#date
			date_ = soup.find('p', {"class": "publish_date"})
			if date_ :
				date_str=date_.get_text().replace("\n","").replace("  ","").split(",")[0]
				claim_.setDate(dateparser.parse(date_str).strftime("%Y-%m-%d"))

			#title
			title=soup.findAll("h1")
			claim_.setTitle(title[1].text)


			#body
			body=soup.find("article")
			claim_.setBody(body.get_text().replace("\n","").replace("TwitterFacebookE-mailWhatsApp",""))

			#related links
			divTag = soup.find("article").find("hr")
			related_links=[]
			for link in divTag.find_all_next('a', href=True):
			    related_links.append(link['href'])
			claim_.setRefered_links(related_links)
			

			#claim
			claim_.setClaim(str(claim_element.get_text().encode('utf-8')).replace("\n",""))
			#record['claim']="dddd"
			#conclusin
			if (claim_element.find_previous_sibling("figure") and claim_element.find_previous_sibling("figure").find("figcaption")):
				claim_.setConclusion(claim_element.find_previous_sibling("figure").find("figcaption").get_text())


			claims.append(claim_.getDict())

    #creating a pandas dataframe
	pdf=pd.DataFrame(claims)
	return pdf