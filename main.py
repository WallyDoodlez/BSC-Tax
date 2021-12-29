import requests
import constants as Constants
import pandas as pd
from utility import RenderJSON
import utility as Utility
import numpy as np
import cmcpaths as CMCPaths
import api as API
from binancebridge import BinanceBridgeAPI
import os
import binance as Binance
import json
import pcs



def apply_subgroup(group):
    this_group_attr_tx_from = group.loc[(group["from"] == lower_addr)]

    this_group_attr_tx_to = group.loc[(group["to"] == lower_addr)]
  #  print(len(this_group_attr_tx_to)
    total_received = this_group_attr_tx_to.value.sum()
    total_sent = this_group_attr_tx_from.value.sum()
    total_recieved_name = "total_recieved_" + group.tokenSymbol
    total_sent_name = "total_sent_" + group.tokenSymbol
    #print(total_received)
    return [total_received, total_sent]


def apply_group(group):
    token_groups = group.groupby("tokenSymbol")    
    #print(token_groups)
    sub_result = token_groups.apply(apply_subgroup)
 #   print(sub_result)
    return []



def getPoolInfos(is_purge_cache):    


    if (not is_purge_cache and os.path.exists(Constants.token_info_filename)):
        tokens_info = pd.read_csv(Constants.token_info_filename)
        return tokens_info

    
    #-- get binance bridge token infos
    bb = BinanceBridgeAPI()
    binance_bridge_tokens = bb.get_tokens()
    binance_bridge_tokens = pd.DataFrame(binance_bridge_tokens["data"]["tokens"])
    binance_bridge_tokens = binance_bridge_tokens[["bscSymbol","ethSymbol","name","bscContractAddress", "ethContractAddress"]]
    binance_bridge_tokens["transaction_type"] = "Transfer with Binance Bridge"

    #-- gets Venus token info
    venus_tokens = API.retrieveVenusTokenInfo()
    venus_tokens["ethSymbol"] = None
    venus_tokens["transaction_type"] ="Interact with Venus"
    tokens_info = pd.concat([venus_tokens, binance_bridge_tokens])

    #-- gets Beefy pools info
    beefy_pools = API.getBeefyPoolsInfo()
    beefy_pools.rename(columns={"earnContractAddress": "bscContractAddress", "token": "bscSymbol"}, inplace=True)
    beefy_pools["ethSymbol"] = None
    beefy_pools["transaction_type"] = "Interact with Beefy"
    beefy_pools = beefy_pools[["bscContractAddress" , "bscSymbol", "name", "ethSymbol", "transaction_type"]]
    beefy_pools["bscContractAddress"] = beefy_pools["bscContractAddress"].str.lower()
    tokens_info = pd.concat([tokens_info, beefy_pools])

    
    


    #--get auto farm token infos (WIP)
    #auto_farm_info = API.getAutofarmInfo()


    tokens_info.to_csv(Constants.token_info_filename)
    return tokens_info


#get all the poolinfos
tokens_info = getPoolInfos(True)

pd.set_option('display.max_colwidth', -1)

# param = dict(addr = Constants.addr, token = Constants.api_token)
# get_url = Constants.get_tx.format_map(param)
# get_internal_tx_param = dict(txhash = '0x8521d8095b60e62da195aba25aa36833134c1ee5e9947d587578a713e2bc9180', token = Constants.api_token)
# get_internal_tx_url = Constants.get_internal_tx.format_map(get_internal_tx_param)

get_tx_param = dict(addr = Constants.addr, token = Constants.api_token, sort="asc")
get_tokentx_url = Constants.get_token_tx.format_map(get_tx_param)
get_tx_url = Constants.get_tx.format_map(get_tx_param)

r = requests.get(get_tokentx_url)
r_json = r.json()

#get all the token tx
token_tx_df = pd.DataFrame(r_json["result"])
token_tx_df["value"] = token_tx_df.apply(lambda x: x["value"][:-int(x["tokenDecimal"])] + "." + x["value"][-int(x["tokenDecimal"]):], axis=1)
token_tx_df.drop(["input", "tokenDecimal" ],axis=1, inplace=True)
token_tx_df = token_tx_df[["nonce", "hash", "timeStamp", "tokenSymbol", "contractAddress", "from", "to", "gas", "value", "tokenName", "gasPrice", "gasUsed"]]
token_tx_df = token_tx_df.astype({"timeStamp": "int32", "nonce": "int32", "gasPrice": "float64", "gasUsed": "int64", "value":"float64", "gas": "int64"}, copy=False)
#gas cost is in BNB/ETH
token_tx_df["gasCost"] = token_tx_df.apply(lambda x: x["gasPrice"] * x["gasUsed"] / 10**Constants.WEI_DECIMALS, axis=1)


#use local file for now
#r = requests.get(get_tx_url)
#r_json = r.json()
r_json =  None
with open("bsc_tx.json", "r") as f:
    r_json = json.load(f)


#get all the non token tx
tx_df = pd.DataFrame(r_json["result"])
tx_df = tx_df[tx_df["isError"] == "0"]
tx_df = tx_df[["nonce" , "hash", "timeStamp", "from", "to", "gas", "value", "gasPrice", "gasUsed"]]
tx_df["value"] = tx_df.apply(lambda x: x["value"][:-18] + "." + x["value"][-18:], axis=1)
tx_df = tx_df.astype({"timeStamp": "int32", "nonce": "int32", "gasPrice": "float64", "gasUsed": "int64", "gas": "int64","value":"float64", })
#gas cost is in BNB/ETH
tx_df["gasCost"] = tx_df.apply(lambda x: x["gasPrice"] * x["gasUsed"] / 10**Constants.WEI_DECIMALS, axis=1)
tx_df["tokenName"] ="Binance coin"
tx_df["tokenSymbol"] ="BNB"

unique_hashes = token_tx_df["hash"].unique()
missing_tx_entires = tx_df[~tx_df["hash"].isin(unique_hashes)]

all_tx = pd.concat([token_tx_df, tx_df])
all_tx.sort_values(by=["timeStamp"], inplace=True)
all_tx.reset_index(inplace=True)
#df =df.head()
hash_group = all_tx.groupby("timeStamp")

#df.head()

lower_addr = Constants.addr.lower()

pcs_contract_addresses = API.getPancakeSwapRouterContracts()

new_data = []
no_value_tx = []
for ts, gp in hash_group:
    sent_ts = gp[gp["from"] == lower_addr]
    recvd_ts = gp[gp["to"] == lower_addr]
    sent_ts_token_group = sent_ts.groupby("tokenSymbol")
    recvd_ts_token_group = recvd_ts.groupby("tokenSymbol")

    if ( len(gp) == 1 and gp.iloc[0]["value"] == 0) :
        single_tx = gp.iloc[0]
        #if the hash_group is just a single transfer without any value, then we mark is as "No value Tx"
        tx_hash = single_tx["hash"]
        from_addr = single_tx["from"]
        to_addr = single_tx["to"]
        token_symbol = single_tx["tokenSymbol"]
        total_value = single_tx["value"]
        bsc_contract = single_tx["contractAddress"]
        direction = "sent" if from_addr == lower_addr else "recvd"
        from_to = from_addr if to_addr == lower_addr else to_addr
        no_value_tx.append({"txHash": tx_hash, "timeStamp": ts, "direction": direction, "tokenSymbol": token_symbol, "value": total_value, "tokenContractAddress": bsc_contract, "from_to":from_to})
        continue

    #check if the hash group contains a to or from address to PCS router
    has_pcs_contract_txs_from = gp["from"].isin(pcs_contract_addresses).any()
    has_pcs_contract_txs_to = gp["to"].isin(pcs_contract_addresses).any()
    description = None
    
    if (has_pcs_contract_txs_from or has_pcs_contract_txs_to ):
        pcs_swap_from = gp.loc[(gp["from"] == lower_addr) & (gp["tokenSymbol"] != "BNB")].iloc[0]
        pcs_swap_to = gp.loc[(gp["to"] == lower_addr) & (gp["tokenSymbol"] != "BNB")].iloc[0]
        description = "Swap with PCS from {swap_from_value}{swap_from_tokenSymbol} to {swap_to_value}{swap_to_tokenSymbol}".format_map({
            "swap_from_value" : pcs_swap_from["value"],
            "swap_to_value": pcs_swap_to["value"],
            "swap_from_tokenSymbol": pcs_swap_from["tokenSymbol"],
            "swap_to_tokenSymbol": pcs_swap_to["tokenSymbol"]
        })
        gp["transaction_type"] = "Swap with PCS"
        gp["description"] = description
    
    if (description is None and len(sent_ts_token_group) == 2 and len(recvd_ts_token_group) == 1):
        lp_info = pcs.query_pair(recvd_ts_token_group["contractAddress"])
        if (lp_info is not None):
            gp["transaction_type"] = "PCS liquidity in "
            description = "Provide {token0} and {token1} for swap pool".format_map(lp_info)

    
            
    


    tokens_recvd = {}
    

    for token_symbol, token_group in sent_ts_token_group:
        total_value = token_group.value.sum()
        bsc_contract = token_group.contractAddress.iloc[0]
        tokens_recvd[token_symbol] = total_value
        tx_hash = token_group["hash"].iloc[0]
        from_addr = token_group["to"].iloc[0]
        new_data.append({"txHash": tx_hash, "timeStamp": ts, "direction": "sent", "tokenSymbol": token_symbol, "value": total_value, "tokenContractAddress": bsc_contract, "from_to":from_addr})


    
    tokens_sent = {}
    for token_symbol, token_group in recvd_ts_token_group:
        total_value = token_group.value.sum()
        tokens_sent[token_symbol] = total_value
        bsc_contract =token_group.contractAddress.iloc[0]
        tx_hash = token_group["hash"].iloc[0]
        to_addr = token_group["from"].iloc[0]
        new_data.append({"txHash": tx_hash, "timeStamp": ts, "direction": "recvd", "tokenSymbol": token_symbol, "value": total_value, "tokenContractAddress": bsc_contract, "from_to": to_addr})

new_data_df = pd.DataFrame(new_data)
new_data_df["epoch"] = new_data_df["timeStamp"]
new_data_df["timeStamp"] = pd.to_datetime(new_data_df["timeStamp"], unit="s")
#match binance's hot wallet
binance_info = API.getBinanceExchangeInfo()
new_data_df.loc[new_data_df["from_to"].isin(binance_info["hotwallets"]), "transaction_type"] = "Binance bridge"



no_value_tx_df = pd.DataFrame(no_value_tx)
no_value_tx_df["epoch"] = no_value_tx_df["timeStamp"]
no_value_tx_df["timeStamp"] = pd.to_datetime(no_value_tx_df["timeStamp"], unit="s")
no_value_tx_df["transaction_type"] = "TX with no value"

#join the data with the pool_info
new_data_df = pd.merge(new_data_df, tokens_info, left_on = "from_to", right_on ="bscContractAddress", how="left")
new_data_df["transaction_type"] = new_data_df["transaction_type_x"] 
new_data_df["transaction_type"] = new_data_df["transaction_type_y"] 
new_data_df = pd.concat([new_data_df, no_value_tx_df])
new_data_df.sort_values(by=["timeStamp"], inplace=True)

#get history from binance and match with TX (wip)



new_data_df = new_data_df[["txHash","timeStamp","direction","tokenSymbol","value","tokenContractAddress", "from_to", "epoch","bscContractAddress", "name", "transaction_type","ethContractAddress"]]
new_data_df["description"] = None
unique_tokens = new_data_df[["tokenSymbol", "tokenContractAddress"]].drop_duplicates()

new_data_df.sort_index(axis=1, inplace=True)
smallest_timestamp = new_data_df.iloc[0]["epoch"]
largest_timestamp = new_data_df.iloc[len(new_data_df)-1]["epoch"]


#get the binance deposit history
binance_deposit = Binance.get_deposit_histories(smallest_timestamp*1000 , largest_timestamp*1000 )
binance_withdraws = Binance.get_withdraw_histories(smallest_timestamp*1000 , largest_timestamp*1000 )
binance_withdraws_txid = binance_withdraws["txId"]
new_data_df.loc[new_data_df["txHash"].isin(binance_withdraws_txid), "transaction_type"] = "recieved from binance"
binance_deposit_txid = binance_deposit["txId"]
new_data_df.loc[new_data_df["txHash"].isin(binance_deposit_txid),"transaction_type"]= "sent to binance"




prices = {}
unknown_tokens = []
unique_tokens["err"] = None
unique_tokens["token_info"] = None

def apply_token_info(row):
    result = API.geckoGetCryptoInfo(row["tokenSymbol"], row["tokenContractAddress"])
    row["token_info"] = result[0]
    row["err"] = result[1]
    return row

unique_tokens = unique_tokens.apply(apply_token_info, axis=1 ) 

for index,info in unique_tokens.iterrows():
    result = API.geckoGetHistoricalPrice(info["token_info"], smallest_timestamp, largest_timestamp)
    if result is not None and len(result) > 0 :
        prices[info["tokenSymbol"]] = result

print(prices)

def resolve_fiat_value(row):
    target_token = row["tokenSymbol"]
    result = None
    if target_token not in prices.keys():
        return row

    else:
        transaction_timestamp = row.epoch
        result = API.getInterpolatedHistoricalPrice(prices[target_token], transaction_timestamp)
    
    row["token_fiat_price"] = result
    row["fiat_value"] = result * row["value"]

    return row

new_data_df["fiat_value"] = None
new_data_df["token_fiat_price"] = None
new_data_df = new_data_df.apply(resolve_fiat_value, axis = 1)
new_data_df.set_index(["txHash", "tokenSymbol"], inplace=True)
new_data_df
