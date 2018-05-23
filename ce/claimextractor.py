import pandas as pd
current_websites={
	"english":["fullfact"],
	"portuguese":["aosfatos","lupa"] 
}

def get_sites():
	print current_sites


def get_claims(criteria):
	if (criteria.website):
		module = __import__(criteria.website)
		func = getattr(module, "get_all_claims")
		pdf = func(criteria)
		pdf.to_csv(criteria.output, encoding="utf8")

	else:
		pdfs=[]
		language  = criteria.language
		for website in current_websites[language]:
			module = __import__(website)
			func = getattr(module, "get_all_claims")
			pdfs.append( func(criteria))

		pd.concat(pdfs).to_csv(criteria.output, encoding="utf-8")




