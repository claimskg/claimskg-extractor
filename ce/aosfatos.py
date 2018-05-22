import pandas as pd
import urllib2
from bs4 import BeautifulSoup
import datetime
import dateparser
import copy


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

		for claim_ in soup.findAll("blockquote"):

			record={}
			record['url']=url_complete
			record['source']="aosfatos"
			record['claim']=""
			record['body']=""
			record['conclusion']=""
			record['refered_links']=""
			record['title']=""
			record['date']=""



			#date
			date_ = soup.find('p', {"class": "publish_date"})
			if date_ :
				date_str=date_.get_text().replace("\n","").replace("  ","").split(",")[0]
				record['date']=dateparser.parse(date_str).strftime("%Y-%m-%d")

			#title
			title=soup.findAll("h1")
			record['title']=title[1].text


			#body
			body=soup.find("article")
			record['body']=body.get_text().replace("\n","")

			#related links
			divTag = soup.find("article").find("hr")
			related_links=[]
			for link in divTag.find_all_next('a', href=True):
			    related_links.append(link['href'])
			record['refered_links']=related_links



			#verifing how many clains have
			

			#claim
			record['claim']=str(claim_.get_text().encode('utf-8')).replace("\n","")
			#record['claim']="dddd"
			#conclusin
			if (claim_.find_previous_sibling("figure") and claim_.find_previous_sibling("figure").find("figcaption")):
				record['conclusion']= claim_.find_previous_sibling("figure").find("figcaption").get_text()

			claims.append(record)




		




    
    #creating a pandas dataframe
	pdf=pd.DataFrame(claims)
	return pdf