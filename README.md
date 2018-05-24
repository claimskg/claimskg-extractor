## Fact-Checking
### English
- fullfact https://fullfact.org/
- snopes https://www.snopes.com/ [under implementation]
- polifact http://www.politifact.com/ [under implementation]
### Portuguese
- Lupa – http://piaui.folha.uol.com.br/lupa/ 
- Aos Fatos – https://aosfatos.org/aos-fatos-e-noticia/ 
- Publica – https://apublica.org/checagem/ 
- G1 - https://g1.globo.com/e-ou-nao-e/




## features

- "Claim"					: Textual claim which is being verified
- "Credibility"			: true/false
- "URL"					: URL of the corresponding source page
- "body"			: Description provided by the source article about why the claim is true or false
- "Date"	: Date when the article was published
- "Referred Links"		: References used for verifying the claim.
- "Tags"					: Set of tags provided on the Snope article (seperated by semicolon)

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
