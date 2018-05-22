## Fact-Checking
### English
- fullfact.org 
- snopes.com [under implementation]
### Portuguese
- Lupa – http://piaui.folha.uol.com.br/lupa/ [under implementation]
- Aos Fatos – https://aosfatos.org/aos-fatos-e-noticia/ [under implementation]
- Publica – https://apublica.org/checagem/ [under implementation]




## features

- "Claim"					: Textual claim which is being verified
- "Credibility"			: true/false
- "URL"					: URL of the corresponding snopes page
- "Origins"				: Description of how the claim was originated. Corresponds to the "Origin" section in the Snopes - - article
- "Example"				: Example of how Snopes spotted the claim. Corresponds to the "Example" section in the Snopes -  -- article
- "Description"			: Description provided in the Snopes article about why the claim is true or false
- "Date"	: Date when the Snopes article was published
- "Referred Links"		: References used for verifying the claim. Corresponds to "Sources" section in the Snopes article
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
