import pandas as pd
import urllib2
from BeautifulSoup import BeautifulSoup
import datetime

def get_all_claims():

	#performing a search by each letter, and adding each article to a urls_ var.


	now = datetime.datetime.now()


	urls_={}
	for year in range (2015,now.year+1):
	    for month in range (1,13):
	        try:
	            page = urllib2.urlopen("http://piaui.folha.uol.com.br/lupa/"+str(year)+"/"+str(month)+"/").read()
	        except:
	            break
	        soup = BeautifulSoup(page)
	        soup.prettify()

	        links = soup.find('div', {"class": "lista-noticias"}).findAll('a', href=True)
	        if len(links) != 0:
	            for anchor in links:
	            	if (anchor['href'] not in urls_.keys()):
		                urls_[anchor['href']]=[year,month]
		            	print "adding "+str(anchor['href'])
	            #[l,page_number]
	        else:
	            print ("break!")
	            break

	claims=[]
	index=0
	# visiting each article's dictionary and extract the content.
	for url in urls_.keys():
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
	    


		url_complete=url
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
		conclusion=soup.find('div', {"class": "etiqueta"})
		if conclusion :
			record['conclusion']=str(conclusion)

		    
		    
		#title
		title=soup.find("h2", {"class": "bloco-title"})
		record['title']=title.text


		#related links
		divTag = soup.find("div", {"class": "post-inner"})
		related_links=[]
		for link in divTag.findAll('a', href=True):
		    related_links.append(link['href'])
		record['related_links']=related_links



		claims.append(record)
    
    #creating a pandas dataframe
	pdf=pd.DataFrame(claims)
	return pdf