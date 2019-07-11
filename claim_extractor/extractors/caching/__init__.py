from typing import Dict, Optional

import requests
from redis import Redis
from requests.packages import urllib3

from claim_extractor import Claim

redis = Redis(decode_responses=True)


def get(url: str, headers: Dict[str, str] = None, timeout: int = None):
    page_text = redis.get(url)
    try:
        if not page_text:
            result = requests.get(url, headers=headers, timeout=timeout)
            if result.status_code < 400:
                page_text = result.text
                redis.set(url, page_text)
            else:
                return None
    except urllib3.exceptions.ReadTimeoutError:
        page_text = None
    except requests.exceptions.ReadTimeout:
        page_text = None
    except requests.exceptions.MissingSchema:
        page_text = None
    return page_text

def head(url: str, headers: Dict[str, str] = None, timeout: int = None):

    page_text = redis.get(url)
    try:
        if not page_text:
            r = requests.head(url)
            if(3 <= r.status_code/100 < 4):
                url = r.headers['Location']
                x = {'url' : url, 'status_code' : 200, 'text' : ''}
            elif result.status_code < 300:
                x = {'url' : result.url, 'status_code' : result.status_code}
            else:
                x = {'url' : url, 'status_code' : result.status_code}
        else:
            x = {'url' : url, 'status_code' : 200}
        return x
    except urllib3.exceptions.ReadTimeoutError:
        page_text = None
    except requests.exceptions.ReadTimeout:
        page_text = None
    except requests.exceptions.MissingSchema:
        page_text = None

    x = {'url' : url, 'status_code' : 1000}

    return x

def get_claim_from_cache(url: str) -> Optional[Claim]:
    result = redis.hgetall("___cached___claim___" + url)
    if result:
        claim = Claim.from_dictionary(result)
        return claim
    else:
        return None


def cache_claim(claim: Claim):
    dictionary = claim.generate_dictionary()
    url = claim.url
    redis.hmset("___cached___claim___" + url, dictionary)
