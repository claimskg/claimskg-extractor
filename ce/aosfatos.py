import pandas as pd
import urllib2
from BeautifulSoup import BeautifulSoup
import datetime

def get_all_claims():

	#performing a search by each letter, and adding each article to a urls_ var.


	now = datetime.datetime.now()


	urls_={}
	for type_ in ["verdadeiro","impreciso","exagerado","contraditorio","insustentavel","falso"]:
		for page_number in range (1,500):
			try:
				print "http://aosfatos.org/noticias/checamos/"+str(type_)+"/?page="+str(page_number)
				page = urllib2.urlopen("http://aosfatos.org/noticias/checamos/"+str(type_)+"/?page="+str(page_number)).read()
			except:
				break
			soup = BeautifulSoup(page)
			soup.prettify()

			links = soup.findAll('a',{"class":"card third"}, href=True)
			if len(links) != 0:
				for anchor in links:
					if (anchor['href'] not in urls_.keys()):
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
		record={}
		record['claim']=""
		record['conclusion']=""
		record['related_links']=""
		record['origin_links']=""
		record['title']=""
		record['date']=""
		record['url']=""
	    


		url_complete="https://aosfatos.org/"+str(url)
		record['url']=url_complete
		#print url_complete
		page = urllib2.urlopen(url_complete).read()
		soup = BeautifulSoup(page)
		soup.prettify()

		#orign_links
		quote_links=[]
		if (soup.find('blockquote')):
		    for link in soup.find('blockquote').findAll('a', href=True):
		        quote_links.append(link['href'])
		record['origin_links']=quote_links

		#claim
		claim = soup.find('div', {"class": "col-xs-12 col-sm-6 col-left"})
		if claim :
		    record['claim']=str(claim)


		#conclusin
		record['conclusion']=str(conclusion)


		#date
		date = soup.find('p', {"class": "publish_date"})
		if date :
		    record['date']=str(date)

		

		#title
		title=soup.findAll("h1")
		record['title']=title[1].text


		# #related links
		# divTag = soup.find("hr").next_sibling
		# related_links=[]
		# for link in divTag.findAll('a', href=True):
		#     related_links.append(link['href'])
		# record['related_links']=related_links



		claims.append(record)
    
    #creating a pandas dataframe
	pdf=pd.DataFrame(claims)
	return pdf