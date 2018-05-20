- **Main:** Examples of how to use.

- **Exporter:** Export tweets to a csv file named "output_got.csv".

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
