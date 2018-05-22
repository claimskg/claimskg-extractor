## Fact-Checking
### English
- fullfact.org 
- snopes.com [under implementation]
### Portuguese
- Lupa – http://piaui.folha.uol.com.br/lupa/ [under implementation]
- Aos Fatos – https://aosfatos.org/aos-fatos-e-noticia/ [under implementation]
- Publica – https://apublica.org/checagem/ [under implementation]




## features

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
Export claims to a csv file named "output_got.csv".
- Get help use
```
    python Exporter.py -h
``` 
- Get claims by website
```
    python Exporter.py --website "fullfact"
