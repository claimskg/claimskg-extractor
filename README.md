# Fact-Checking
- fullfact.org 
- snopes.com [under implementation]


# features

- claim
- conclusion
- related_links
- title
- date
- url

## Examples of python usage
- Get claims by website
``` python
	import ce.claimextractor as ce
  	pdf = ce.get_claims("fullfact")
	pdf.head()
  
```    

## Examples of command-line usage
- Get help use
```
    python Exporter.py -h
``` 
- Get claims by website
```
    python Exporter.py --website "fullfact"
