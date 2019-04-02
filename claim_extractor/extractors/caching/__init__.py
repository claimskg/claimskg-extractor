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
