import importlib

import pandas
from lxml.html.clean import Cleaner

cleaner = Cleaner()
cleaner.javascript = True  # This is True because we want to activate the javascript filter
cleaner.style = True  # This is True because we want to activate the styles & stylesheet filter
cleaner.page_structure = True

default_label = "OTHER"

count_ = 0
current_websites = {
    "english": ["snopes", "politifact", "truthorfiction", "checkyourfact", "factscan", "africacheck"],
    "portuguese": ["aosfatos", "lupa", "publica", "g1", "efarsas"],
    "german": ["mimikama", "correctiv"]
}

current_websites_invert = {}
for key in list(current_websites.keys()):
    for web_ in current_websites[key]:
        current_websites_invert[web_] = key

spacy_portuguese = None
spacy_english = None
spacy_germam = None


def get_sites():
    print(current_websites)


def get_claims(configuration):
    if configuration.website:
        websites = []
        split_list = configuration.website.split(",")
        if len(split_list) > 0:
            websites += split_list
        else:
            websites.append(configuration.website)

        output_data = []
        for web in configuration.website.split(","):
            module = importlib.import_module("." + web,
                                             "claim_extractor.extractors")
            extractor_class = getattr(module, web.capitalize() + "FactCheckingSiteExtractor")
            extractor_instance = extractor_class(configuration)  # type : FactCheckingSiteExtractor
            claims = extractor_instance.get_all_claims()
            output_data.append(claims)
        data_frame = pandas.concat(output_data)
        data_frame.to_csv(configuration.output, encoding="utf-8")
