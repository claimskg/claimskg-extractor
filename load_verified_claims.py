from tqdm import tqdm
from elasticsearch import Elasticsearch

import pandas as pd
import utils
import csv
import json
from pip._vendor.distlib.util import CSVReader
from lxml.etree import indent
from csv import DictReader
import sys



TEST = True

if TEST:
    USERNAME = ''
    PASSWPRD = ''
    ELASTICSEARCH_SERVER = '127.0.0.1'
    PORT = 9200
else:
    USERNAME = 'elastic'
    PASSWPRD = 'qcri1234!!!!'
    ELASTICSEARCH_SERVER = '23.99.190.106'
    PORT = 9200

if USERNAME:
    es =  Elasticsearch(['http://%s:%s@%s:%d'%(USERNAME, PASSWPRD, ELASTICSEARCH_SERVER, PORT)])
else:
    es =  Elasticsearch(['http://%s:%d'%(ELASTICSEARCH_SERVER, PORT)])


csvFilePath = 'output_got_DB.csv'
data={}
verified_claims=[]
with open(csvFilePath, encoding='utf-8') as csvFile:
    csvReadFile=csv.DictReader(csvFile)
    for rows in csvReadFile:
        readrows=rows['number']
        data[readrows]=rows

        verified_claims.append(data[readrows])

try:

    for i, verified_claim in enumerate(tqdm(verified_claims)):
        if not es.exists(index=verified_claim['claimReview_source'], id=i):
            es.create(index=verified_claim['claimReview_source'], id=i, body=verified_claim)
except Exception as e1:
    print(e1.info)
