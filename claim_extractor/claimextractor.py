import importlib

import pandas
from lxml.html.clean import Cleaner

import export_rdf as e_rdf

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
    def delete_unamed_col(pdf):
        un_col = []
        index_ = -1
        for c in pdf.columns:
            index_ += 1
            # print str(c)
            if "Unnamed:" in c:
                # print "drop"+c
                un_col.append(index_)

        pdf = pdf.drop(pdf.columns[un_col], axis=1)
        return pdf

    if configuration.update_db:
        input_data_frame = pandas.read_csv(configuration.input, encoding="utf8")
        configuration.avoid_url = input_data_frame['claimReview_url'].values

        configuration.output = configuration.input
        if configuration.website and len(configuration.website.split(",")) > 1:
            output_data = []
            for web in configuration.website.split(","):
                module = __import__(web)
                func = getattr(module, "get_all_claims")
                output_data.append(func(configuration))
            aggregated_data_frame = pandas.concat(output_data)
            aggregated_data_frame = delete_unamed_col(aggregated_data_frame)
            input_data_frame = delete_unamed_col(input_data_frame)
            data_frame = pandas.concat([input_data_frame, aggregated_data_frame], ignore_index=True)
            data_frame = delete_unamed_col(data_frame)

        elif configuration.language:
            output_data = []
            for website in current_websites[configuration.language]:
                module = __import__(website)
                func = getattr(module, "get_all_claims")
                output_data.append(func(configuration))
            aggregated_data_frame = pandas.concat(output_data)
            aggregated_data_frame = delete_unamed_col(aggregated_data_frame)
            input_data_frame = delete_unamed_col(input_data_frame)
            data_frame = pandas.concat([input_data_frame, aggregated_data_frame], ignore_index=True)
            data_frame = delete_unamed_col(data_frame)

    elif configuration.website:
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

    elif configuration.input:
        data_frame = pandas.read_csv(configuration.input, encoding="utf8")

    else:
        output_data = []
        language = configuration.language
        for website in current_websites[language]:
            module = __import__(website)
            func = getattr(module, "get_all_claims")
            output_data.append(func(configuration))
        data_frame = pandas.concat(output_data)

    if configuration.since:
        data_frame = data_frame[data_frame['claimReview_datePublished'] >= configuration.since]

    if configuration.until:
        data_frame = data_frame[data_frame['claimReview_datePublished'] <= configuration.until]

    if configuration.rdf:
        out = e_rdf.export_rdf(data_frame, configuration)
        file = open(str(configuration.output) + "." + str(configuration.rdf), "w")
        file.write(out)

    data_frame.to_csv(configuration.output, encoding="utf-8")


def normalize_credibility(pdf):
    pdf["rating_alternateName_normalized"] = ""
    return pdf
