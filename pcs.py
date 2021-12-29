import api as API
import constants as Constants
import json
import pandas as pd

CACHE_NAME = "pcs_pair"
CACHE_SHEET_NAME = "pair_contract"

pair_cache = API.get_cache(CACHE_NAME, CACHE_SHEET_NAME)
if (pair_cache is None):
    pair_cache = pd.DataFrame(columns = ["pair", "token0", "token1", "token0_contract", "token0_contract"])
pair_cache.set_index("pair", inplace=True)



def query_pair(pair_contract_id):
    global pair_cache
    pair_info = pair_cache.loc[pair_contract_id]  if pair_contract_id in pair_cache.index else None
    if (pair_info is not None):
        return {
            "pair": pair_contract_id, 
            "token0": pair_info["token0"], 
            "token1": pair_info["token1"], 
            "token0_contract": pair_info["token0_contract"], 
            "token1_contract": pair_info["token1_contract"]
        }
    

    graph_query = """{{
       pair(id: "{pair}") {{
            token0 {{
                symbol
                id
            }},
            token1 {{
                symbol
                id
            }}
        }}
    }}
        """
    
    query_data = {
        "query": graph_query.format(pair = pair_contract_id)
    }
    result = API.webPostReuqestJSON(Constants.pcs_subgraph_url, data=  json.dumps(query_data))
    if (result["data"]["pair"] is None):
        return None
    else:
        pair_info = result["data"]["pair"]
        pair_result = {"pair": pair_contract_id, "token0": pair_info["token0"]["symbol"], "token1": pair_info["token1"]["symbol"], "token0_contract": pair_info["token0"]["id"], "token1_contract": pair_info["token1"]["id"]}
        pair_result_df = pd.DataFrame([pair_result]);
        pair_result_df.set_index("pair", inplace=True)
        if (len(pair_cache) == 0 ):
            pair_cache = pair_result_df
        else:
            pair_cache = pd.concat([pair_cache, pair_result_df])
        API.set_cache(CACHE_NAME, pair_cache, CACHE_SHEET_NAME)
        return pair_result
    
