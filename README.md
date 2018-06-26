## Fact-Checking
One valuable instrument to verify the truthfulness of a claim is Fact-checking. Usually, Fact-checking is a non-profit organization that provides an independent investigation about questionable facts. Besides providing free tools, information, and advice, it is the rich knowledge base that can be used to train computational models to detect this type of fake content automatically.


We are just starting, and there are still several things to be done (and issues to be solved). So if you want to contribute to a nice project, welcome aboard!!

* We just use websites considered by the fact checking community as highly reputable https://www.poynter.org/international-fact-checking-network-fact-checkers-code-principles .

### Portuguese
Although the Fact-checking is not new (for instance, snopes.com has been active for more than 10 years), unfortunately, these initiatives are still young and scared for Portuguese. Some of prominent Brazilian Fact-checking are:


- Lupa – http://piaui.folha.uol.com.br/lupa/
- Aos Fatos – https://aosfatos.org/aos-fatos-e-noticia/
- Publica – https://apublica.org/checagem/
- G1 - https://g1.globo.com/e-ou-nao-e/
- E-farsas - http://www.e-farsas.com/

Currently, we have extracted 1463 claims from these Brazilian fact-checking.

### English

- Fullfact - https://fullfact.org/
- Snopes - https://www.snopes.com/
- Politifact - http://www.politifact.com/
- TruthOrFiction - http://TruthOrFiction.com
- Checkyourfact - http://checkyourfact.com

We have extracted 27594 claims from these websites.

### German

- Mimika - https://www.mimikama.at/
- Correctiv - https://correctiv.org/

We extracted 5193 claims from german websites.



## Features Extracted

- "Claim"					: Textual claim which is being verified
- "Credibility"			: true/false
- "URL"					: URL of the corresponding source page
- "body"			: Description provided by the source article about why the claim is true or false
- "Date"	: Date when the article was published
- "Referred Links"		: References used for verifying the claim.
- "Tags"					: Set of tags provided on the Snope article (seperated by semicolon)

## Prerequisites
Expected package dependencies are listed in the "requirements.txt" file for PIP, you need to run the following command to get dependencies:
```
pip install -r requirements.txt
```

## Examples of usage

### Python
- Get claims by website
``` python
	import ce.claimextractor as ce
  	pdf = ce.get_claims("fullfact")
	pdf.head()

```    

### Command-line usage
Export claims to a csv file named "output_got.csv".
- Get help use  [under implementation]
```
    python Exporter.py -h
```
- Get claims by website
```
    python Exporter.py --website fullfact,snopes
```
- Get claims by language
```
    python Exporter.py --language portuguese
```
- limit of number of claims
```
    python Exporter.py --language portuguese --maxclaims 30
```
- Extract Entities
```
    python Exporter.py --language portuguese --entity
```
- Extract HTML
```
    python Exporter.py --language portuguese --html
```
## How to cite
Bibtex - https://dl.acm.org/downformats.cfm?id=3201083&parent_id=3201064&expformat=bibtex
```
@inproceedings{woloszyn2018distrustrank,
  title={DistrustRank: Spotting False News Domains},
  author={Woloszyn, Vinicius and Nejdl, Wolfgang},
  booktitle={Proceedings of the 10th ACM Conference on Web Science},
  pages={221--228},
  year={2018},
  organization={ACM}
}
```
