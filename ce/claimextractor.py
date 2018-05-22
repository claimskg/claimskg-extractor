
current_sites={
	"fullfact":"https://fullfact.org/",
}

def get_sites():
	print current_sites


def get_claims(criteria):
	if (criteria.website):
		module = __import__(criteria.website)
		func = getattr(module, "get_all_claims")
		pdf = func(criteria)
		pdf.to_csv(criteria.output, encoding="utf8")



