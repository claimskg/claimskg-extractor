

## ClaimsKG
This project constitutes the web scraping component of ClaimsKG that crawls fact checking sites (mostly taken from https://www.poynter.org/international-fact-checking-network-fact-checkers-code-principles, which holds a list of reliable fact-checking sites) and generates a CSV file with a dump of the extracted information. 

This project is a fork of https://github.com/vwoloszyn/fake_news_extractor that has been refactored and repurposed for the specific needs of ClaimsKG. Most of the original extractors for English-language fact-checking sites have been reimplemented under a new architecture and are the only ones that are functional (see list below). Althrough the original extractors for Portuguese language and German language sites are still present, they haven't yet been integrated, please refer to the orignal implementation if you need to use those. 

### English

- Fullfact - https://fullfact.org/
- Snopes - https://www.snopes.com/
- Politifact - http://www.politifact.com/
- TruthOrFiction - http://TruthOrFiction.com
- Checkyourfact - http://checkyourfact.com
- FactsCan - http://factscan.ca/
- AfricaCheck - https://africacheck.org/

See the ClaimsKG dataset website for statistics (https://data.gesis.org/claimskg/site)



## Features Extracted

- "Claim"			: Textual statement of the claim which is being verified
- "Credibility"			: Truth rating provided by the respective sites in its original form
- "URL"				: URL of the corresponding source page
- "body"			: Description provided by the source article about why the claim is true or false
- "Date"	: 		: Date when the claim was made. 
- "Referred Links"		: References used for verifying the claim.
- "Tags"			: Set of tags or topics provided by the fact checking site.
- "Normalized Credibility"	: FALSE, TRUE, MIXED, OTHER

This version of the extractor doesn't annotate the description and claim with entities on its own, there is a consecutive step to add annotations to the CSV files with TagMe (see tagme fork in the claimskg project group). 

## Prerequisites
This reimplementation runs on Python3.5+. 
Expected package dependencies are listed in the "requirements.txt" file for PIP, you need to run the following command to get dependencies:
```
pip install -r requirements.txt
```

## Examples of usage

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
- limit of number of claims
```
    python Exporter.py --maxclaims 30
```
