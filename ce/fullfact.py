import pandas as pd
import urllib2
from bs4 import BeautifulSoup
import dateparser
import Claim as claim_obj


def get_all_claims(criteria):

	#performing a search by each letter, and adding each article to a urls_ var.

	alfab="bcdefghijklmnopqrstuvxyz"
	urls_={}
	for l in alfab:
	    for page_number in range(1,500):
			if (criteria.maxClaims > 0 and len(urls_)>= criteria.maxClaims):
				break
			try:
				page = urllib2.urlopen("http://fullfact.org/search/?q="+l+"&page="+str(page_number)).read()
			except:
			    break
			soup = BeautifulSoup(page,"lxml")
			soup.prettify()

			links = soup.findAll('a', {"rel": "bookmark"}, href=True)
			if len(links) != 0:
				for anchor in links:
					urls_[anchor['href']]=[l,page_number]
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
		print str(index) + "/" + str(len(urls_))+ " extracting "+str(url)
		index+=1
		claim_ =  claim_obj.Claim()
		claim_.setSource("fullfact")
	    

		try:
			url_complete="http://fullfact.org"+url
			claim_.setUrl(url_complete)
			page = urllib2.urlopen(url_complete).read()
			soup = BeautifulSoup(page,"lxml")
			soup.prettify()

			

			#claim
			claim = soup.find('div', {"class": "col-xs-12 col-sm-6 col-left"})
			if claim :
				claim_.setClaim(claim.get_text().replace("\nClaim\n",""))



			#conclusin
			conclusion = soup.find('div', {"class": "col-xs-12 col-sm-6 col-right"})
			if conclusion :
			    claim_.setConclusion(conclusion.get_text().replace("\nConclusion\n",""))
			    
			    
			#title
			title=soup.find("div", {"class": "container main-container"}).find('h1')
			claim_.setTitle(title.text)


			#date
			date=soup.find("p", {"class": "hidden-xs hidden-sm date updated"})
			claim_.setDate(dateparser.parse(date.get_text().replace("Published:","")).strftime("%Y-%m-%d"))

			
			#body
			body = soup.find("div", {"class": "article-post-content"})
			claim_.setBody(body.get_text())


			#related links
			divTag = soup.find("div", {"class": "row"})
			related_links=[]
			for link in divTag.findAll('a', href=True):
				related_links.append(link['href'])
			claim_.setRefered_links(related_links)



			claims.append(claim_.getDict())
		except:
			print "error=>"+url_complete
    
    #creating a pandas dataframe
	pdf=pd.DataFrame(claims)
	return pdf