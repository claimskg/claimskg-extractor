
current_sites={
	"fullfact":"https://fullfact.org/",
}

def get_sites():
	print current_sites


def get_claims(website):
	module = __import__(website)
	func = getattr(module, "get_all_claims")
	pdf = func()
	pdf.to_csv("output.csv", encoding="utf8")

