# features

- claim
- conclusion
- related_links
- title
- date
- url

## Examples of python usage
- Get tweets by username
``` python
	import claimextractor as ce
  	pdf = ce.get_claims("fullfact")
	pdf.head()
  
```    

## Examples of command-line usage
- Get help use
```
    python Exporter.py -h
``` 
- Get tweets by website
```
    python Exporter.py --website "fullfact"
