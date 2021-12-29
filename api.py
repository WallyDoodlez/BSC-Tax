from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import constants as Constants
import os
from constants import cmc_key
from constants import cmc_web_cookie_key
from constants import venus_api_key
from constants import autofarm_info_url
import cmcpaths as CMCPaths
import time
import json
import pandas as pd
import math
import utility as Utility
import numpy as np
from pycoingecko import CoinGeckoAPI


cmc_cypto_info_cache = {}
cmc_historical_cache_reference = {}
gecko_token_info_cache = None

cg = CoinGeckoAPI()

def get_cache(cache_name, sheet_name):
    cache_file = "{}.xls".format(cache_name)
    cache = None
    if os.path.exists(cache_file):
        try:
            cache = pd.read_excel(cache_file, sheet_name=sheet_name)    
        except ValueError as e:
            cache = None
    return cache

def set_cache(cache_name, dataframe, sheet_name):
    cache_file = "{}.xls".format(cache_name)
    dataframe.to_excel(cache_file, sheet_name = sheet_name)
    
    

def webPostReuqestJSON(url, data, headers = None):
    headers = {} if headers is None else headers

    session = Session()
    session.headers.update(headers)

    try:
        response = session.post(url, data=data)

        data = json.loads(response.text)
        return data
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print (e)
        return None


def webGetRequest(url,  headers, parameters, is_text = False):

#https://stackoverflow.com/questions/64789154/how-can-i-use-the-post-api-using-pyodide/64789621#64789621
#can make web requsts directly in pyodide

    headers = {} if headers is None else headers

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        if (is_text):
            return response.text

        data = json.loads(response.text)
        return data
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print (e)
        return None


def cmsWebRequest(path, parameters):
    url = 'https://web-api.coinmarketcap.com' +  path
    
    headers = {
        'Accepts': 'application/json',
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        if ((data["status"]["error_code"] != 0)):
            raise Exception(data["status"])
        return data["data"]
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print (e)
        return None


def cmsRequest(path, parameters, apiKey = cmc_key):

    url = 'https://pro-api.coinmarketcap.com' +  path
    
    headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': '{0}'.format(apiKey),
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        if ((data["status"]["error_code"] != 0)):
            raise Exception(data["status"])
        return data["data"]
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print (e)
        return None



def venusRequest(path, parameters, apiKey = venus_api_key):
    
    url = 'https://api.venus.io/api/' +  path
    
    headers = {
    'Accepts': 'application/json',
    'venus-api-key': apiKey,
    'Content-Type': 'application/json'
    }

    response = webGetRequest(url, headers, parameters)
    data = response["data"]
    return data
    



def geckoGetHistoricalPrice(token_info, time_start, time_end,  platform_id = Constants.gecko_BSC_platform_id, convert_to ="usd"):
    if token_info is None:
        return None

    data =  cg.get_coin_market_chart_range_by_id(token_info["id"], convert_to, time_start, time_end)
    data = [(x[0], x[1], y[1]) for (x,y) in zip(data["prices"], data["total_volumes"])]
    df = pd.DataFrame(data, columns=["timeStamp", "price", "volume"])
    #df["epoch"] = df["timeStamp"]
    #df["timeStamp"] = pd.to_datetime(df["timeStamp"] / 1000,unit="s")
    df.set_index("timeStamp", inplace=True)
    return df

def getInterpolatedHistoricalPrice(price_table, target_timestamp):
    #target_timeStamp is pandas timestamp   

    #figure out the next closest data point

    closest_time = price_table.index[price_table.index.get_loc(target_timestamp*1000, method="nearest")]
    closest_idx = np.searchsorted(price_table.index,  closest_time)
    closest = price_table.iloc[closest_idx]
    #figure out the next and prev data point to closest 
    next_closest_idx = closest_idx + 1 if len(price_table)>closest_idx+1 else None
    next_closest = price_table.iloc[next_closest_idx] if next_closest_idx is not None else None
    prev_closest_idx = closest_idx - 1 if closest_idx - 1 >= 0 else None
    prev_closest = price_table.iloc[prev_closest_idx] if prev_closest_idx is not None else None
    final_datapoint = None

    if (len(price_table) == 1):
        return closest

    if (closest_time - target_timestamp == 0):
        return closest
    
    time_from_data = None
    time_to_data = None
    time_from = None
    time_to = None
    #check which of next_closest or prev_closest forms an including range with closest to target_timeStamp
    
    if (prev_closest is None and next_closest is not None):
        time_from_data = closest
        time_from = price_table.index[closest_idx]
        time_to_data = next_closest
        time_to = price_table.index[next_closest_idx]
    elif (prev_closest is not None and next_closest is None):
        time_from_data = prev_closest
        time_from = price_table.index[prev_closest_idx]
        time_to_data = closest
        time_to = price_table.index[closest_idx]
    elif (target_timestamp > closest_time / 1000):
        time_from_data = closest
        time_from = price_table.index[closest_idx]
        time_to_data = next_closest
        time_to = price_table.index[next_closest_idx]
    elif (target_timestamp < closest_time / 1000):
        time_from_data = prev_closest
        time_from = price_table.index[prev_closest_idx]
        time_to_data = closest
        time_to = price_table.index[closest_idx]

    time_diff = (time_to - time_from) / 1000
    price_delta = time_to_data["price"] - time_from_data["price"]
    price_delta_per_sec = price_delta/time_diff
    time_diff_from_target = abs(target_timestamp - time_from/1000)
    est_price = time_from_data["price"] + time_diff_from_target * price_delta_per_sec

    return est_price
    # closest_data = price_table.loc[closest].to_dict()
    # closest_data["timeStamp"] = closest
    # return closest_data



def cmcGetHistoricalData(token_name, time_start, time_end, platform_id = Constants.cmc_BSC_platform_id, convert_to = "USD"):
       
    
    #we need at least 1 data point to guess the price
    #first, look for the token info, to get the token ID
    token_info = cmcGetCryptoInfo([token_name])[0]
    token_id = token_info["id"]
    #then, make a query to get the historical data

    this_time_start = time_start
    this_time_end = int(min(time_end, this_time_start + 10000 * 3600 * 4))
    all_results = []
    while (this_time_start < time_end ):
        param = {
            "id": token_id,
            "convert": convert_to,
            "time_start": this_time_start,
            "time_end": this_time_end,
            "time_period": "hourly",
            "interval": "4h",
            "count": 10000    
        }
        api_result = cmsWebRequest(CMCPaths.crypto_history, param)
        this_time_start = this_time_end + 1
        this_time_end = int( min(time_end, this_time_start + 10000 * 3600 * 4))
        all_results = all_results + api_result["quotes"]

    all_results = [x["quote"][convert_to] for x in all_results] 
    df = pd.DataFrame(all_results)
    df["pair"] = token_name + convert_to
    df["timestamp"] = df["timestamp"].apply(Utility.convertISODateTimeToEpoch)
    df.set_index(["pair", "timestamp"] , inplace=True)
    return df
        

    

    
    
    
    
def getEstimatedPrice(token_name, exact_time):
    return None



def geckoGetCryptoInfo(token_name, token_contract_address ,  platform_id = Constants.gecko_BSC_platform_id):
    global gecko_token_info_cache
    if (gecko_token_info_cache is None):
        all_coins =  cg.get_coins_list(include_platform =  'true')
        gecko_token_info_cache =  all_coins
    else:
        all_coins = gecko_token_info_cache

    token_name = token_name.lower()
    warning = None
    filtered_coin = None
    #look for the token address if it exists
    if (token_contract_address is not None):
        filtered_coin = next ((x for x in all_coins if token_contract_address in x["platforms"].values()), None)
        if (filtered_coin is not None):
            return filtered_coin, None

    filtered_coin = [x for x in all_coins if x["symbol"] == token_name]
    

    if (len(filtered_coin) == 1):
        # if there is a single match, just return that one
        return filtered_coin[0], None
    
    #if there are multiple match, match the one with the platform and token_contract_address
    filtered_coin_platform = next((x for x in filtered_coin if platform_id in x["platforms"].keys() and x["platforms"][platform_id] == token_contract_address), None)
    if filtered_coin_platform is None:
        filtered_coin = next((x for x in filtered_coin if Constants.gecko_ETH_platform_id in x["platforms"].keys()), None)
        return filtered_coin, Constants.warnings["001"].format(Constants.gecko_BSC_platform_id, Constants.gecko_ETH_platform_id)
    return filtered_coin_platform, None


def cmcGetCryptoInfo(token_names, platform_id = Constants.cmc_BSC_platform_id):
    
    #creates a new sub cache if its not created for the platform
    if (platform_id not in  cmc_cypto_info_cache):
        cmc_cypto_info_cache[platform_id] = {}
    target_cache = cmc_cypto_info_cache[platform_id]

    #see if there is one piece of data that is outdated
    cache_hits = []
    cache_non_hits = []
    for x in token_names:
        if (x in target_cache):
            cache_hits.append(target_cache[x])
        else:
             cache_non_hits.append(x)
    
    if (len(cache_non_hits) > 0):
        #if there is one piece of data that does not hit the cache, query all the token_names because it costs one api call anyways
        param = {
            'symbol' : ",".join(token_names)
        }
        api_result = cmsRequest(CMCPaths.crypto_id_map, param)
        final_api_result = [y for y in api_result if (y["platform"] is not None and y["platform"]["id"] == platform_id) or (y["platform"] is None and y["rank"] is not None) ]
        for x in final_api_result:
            target_cache[x["symbol"]] = x
        result = final_api_result
    else:
        #if cache hits all, just return the cache
        result = [target_cache[x] for x in token_names]
        
    return result
    

def mcGetHistory(token_id, target_fiat, time_start, time_end):
    param: {
        'convert': target_fiat,
        'id': token_id,
        'start' : time_start,
        'end' : time_end
    }    
    return cmsRequest(CMCPaths.crypto_history, param, cmc_web_cookie_key)


def retrieveVenusTokenInfo():
    data = venusRequest("vtoken",{} )
    data = [{"bscContractAddress" : x["address"], "bscSymbol": x["symbol"], "name": x["name"]} for x in data["markets"]]
    df = pd.DataFrame(data)
    return df


def getBeefyPoolsInfo():
    #data_text = webGetfRequest(Constants.beefy_pools_info_url, None, None, is_text=True)
    json_read = None
    with open(os.path.join(".","poolinfos", "beefypools.json"), "r") as file:
        json_read = json.load(file)
    df = pd.DataFrame(json_read)
    return df

def getAutofarmInfo():
    result = webGetRequest(autofarm_info_url, None, None)
    cleaned_result = [{
        "farmName": x["farmName"],
        "strategy": x["poolInfo"]["strat"],
        "token": x["wantName"],
        "tokenAddress": x["poolInfo"]["want"]

    }]
    df = pd.DataFrame(list(result["pools"].values()))
    return df


def getBinanceExchangeInfo():
    json_read = None
    with open(os.path.join(".","poolinfos", "binance-exchange.json"), "r") as file:
        json_read = json.load(file)
    json_read["hotwallets"] = [ x.lower() for x in json_read["hotwallets"]]
    return json_read



def getPancakeSwapRouterContracts():
    return ['0x05ff2b0db69458a0750badebc4f9e13add608c7f']