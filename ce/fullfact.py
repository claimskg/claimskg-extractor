import pandas as pd
import urllib2
from BeautifulSoup import BeautifulSoup

def get_all_claims(criteria):

	#performing a search by each letter, and adding each article to a urls_fullfact var.

	alfab="bcdefghijklmnopqrstuvxyz"
	urls_fullfact={}
	for l in alfab:
	    for page_number in range(1,500):
	        try:
	            page = urllib2.urlopen("http://fullfact.org/search/?q="+l+"&page="+str(page_number)).read()
	        except:
	            break
	        soup = BeautifulSoup(page)
	        soup.prettify()

	        links = soup.findAll('a', {"rel": "bookmark"}, href=True)
	        if len(links) != 0:
	            for anchor in links:
	                urls_fullfact[anchor['href']]=[l,page_number]
	            	print "adding "+str(anchor['href'])
	            #[l,page_number]
	        else:
	            print ("break!")
	            break

	claims=[]
	index=0
	# visiting each article's dictionary and extract the content.
	for url in urls_fullfact.keys():
		print str(index) + "# extracting "+str(url)
		index+=1
		record={}
		record['claim']=""
		record['conclusion']=""
		record['related_links']=""
		record['origin_links']=""
		record['title']=""
		record['date']=""
		record['url']=""
	    


		url_complete="http://fullfact.org"+url
		record['url']=url_complete
		print url_complete
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
		conclusion = soup.find('div', {"class": "col-xs-12 col-sm-6 col-right"})
		if conclusion :
		    record['conclusion']=str(conclusion) 
		    
		    
		#title
		title=soup.find("li", {"class": "active hidden-xs hidden-sm"})
		record['title']=title.text


		#related links
		divTag = soup.find("div", {"class": "row"})
		related_links=[]
		for link in divTag.findAll('a', href=True):
		    related_links.append(link['href'])
		record['related_links']=related_links



		claims.append(record)
    
    #creating a pandas dataframe
	pdf=pd.DataFrame(claims)
	return pdf