import hmac
import hashlib
import constants
import api as API
import time
import os
import pandas as pd
import time
import datetime
from urllib.parse import urlencode


#signature is always the parameters querystring signed with the secret key
def get_signature(querystring):
    signature = hmac.new(bytes(constants.binance_secret_key, 'latin-1'), msg = bytes(querystring, 'latin-1'), digestmod=hashlib.sha256).hexdigest()
    return signature

def prep_signature(parameters):
    parameters_string = urlencode(parameters)
    signature = get_signature(parameters_string)
    parameters["signature"] = signature

def get_deposit_wallet(symbol):
    parameters = {
        "coin": symbol.upper(),
        "timestamp":  round(time.time() * 1000)
    }

    header = {
        "X-MBX-APIKEY": constants.binance_api_key
    }
    prep_signature(parameters)
    url = constants.binance_api_url + "/sapi/v1/capital//address"
    return API.webGetRequest(url, header, parameters)

def get_withdraw_histories(start_epoch, end_epoch):
    cache = API.get_cache("binance-withdraw", "withdrawal")

    if (cache is not None):
        cache_begins = int(datetime.datetime.strptime(cache.iloc[0]["applyTime"], '%Y-%m-%d %H:%M:%S').timestamp()) * 1000
        cache_ends = int(datetime.datetime.strptime(cache.iloc[-1]["applyTime"], '%Y-%m-%d %H:%M:%S').timestamp()) * 1000  
        if (cache_begins > start_epoch or cache_ends < end_epoch):
            cache = None
    now = int(time.time()) * 1000
    
    if (cache is None):
        #API allows only 90 days intervals
        allowed_intervals = 90 * 24 * 3600 * 1000; 
        current_start_epoch = start_epoch
        header = {
            "X-MBX-APIKEY": constants.binance_api_key
        }
        all_data = []
        while (current_start_epoch < end_epoch):
            current_end_epoch =  min(current_start_epoch + allowed_intervals, now) + 1
            parameters = {
                "timestamp":  round(time.time() * 1000),
                "startTime": current_start_epoch,
                "endTime" : current_end_epoch,
                "recvWindow": 10000
            }    
            current_start_epoch = min(current_start_epoch + allowed_intervals, now)
            prep_signature(parameters)
            url = constants.binance_api_url + "/sapi/v1/capital/withdraw/history"      
            this_data = API.webGetRequest(url, header, parameters)
            all_data = all_data + this_data
        df = pd.DataFrame(all_data)
        API.set_cache("binance-withdraw", df, "withdrawal")
    else:
        df = cache;
    return df  




def get_deposit_histories(start_epoch, end_epoch):
    cache = API.get_cache("binance-deposit", "deposit")

    if (cache is not None):
        cache_begins = cache.iloc[0]["insertTime"]
        cache_ends = cache.iloc[-1]["insertTime"]
        if (cache_begins > start_epoch or cache_ends < end_epoch):
            cache = None
    now = int(time.time()) * 1000
    if (cache is None):        
        #API allows only 90 days intervals
        allowed_intervals = 90 * 24 * 3600 * 1000; 
        current_start_epoch = start_epoch
        header = {
            "X-MBX-APIKEY": constants.binance_api_key
        }
        all_data = []
        while (current_start_epoch < end_epoch):
            current_end_epoch =  min(current_start_epoch + allowed_intervals, now) + 1
            parameters = {
                "timestamp":  round(time.time() * 1000),
                "startTime": current_start_epoch,
                "endTime" : current_end_epoch,
                "recvWindow": 10000
            }    
            current_start_epoch = min(current_start_epoch + allowed_intervals, now)
            prep_signature(parameters)
            url = constants.binance_api_url + "/sapi/v1/capital/deposit/hisrec"      
            this_data = API.webGetRequest(url, header, parameters)
            all_data = all_data + this_data
        df = pd.DataFrame(all_data)
        API.set_cache("binance-deposit", df, "deposit")
    else:
        df = cache
    return df  

