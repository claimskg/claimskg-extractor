import pandas as pd
current_websites={
	"english":["fullfact"],
	"portuguese":["aosfatos","lupa","publica","g1","efarsas"],
	"german":["mimikama"] 
}

def get_sites():
	print current_sites


def get_claims(criteria):
	if (criteria.website):
		if (criteria.website.split(",")>1):
			pdfs=[]
			for web in criteria.website.split(","):
				module = __import__(web)
				func = getattr(module, "get_all_claims")
				pdfs.append( func(criteria))
			pdf = pd.concat(pdfs)
		else:
			module = __import__(criteria.website)
			func = getattr(module, "get_all_claims")
			pdf = func(criteria)
		#pdf.to_csv(criteria.output, encoding="utf8")

	else:
		pdfs=[]
		language  = criteria.language
		for website in current_websites[language]:
			module = __import__(website)
			func = getattr(module, "get_all_claims")
			pdfs.append( func(criteria))
		pdf = pd.concat(pdfs)
	pdf['date'] = pd.to_datetime(pdf['date'], format='%Y-%m-%d')

	if (criteria.since):
		pdf = pdf[pdf['date']>=criteria.since]

	if (criteria.until):
		pdf = pdf[pdf['date']<=criteria.until]

	pdf.to_csv(criteria.output, encoding="utf-8")
