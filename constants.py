api_token = "G3N57ZB3HRRQ7YXMPXMX87XK9UW76B1YBA"
get_tx = "https://api.bscscan.com/api?module=account&action=txlist&address={addr}&endblock=99999999&sort=desc&apikey={token}"
get_internal_tx = "https://api.bscscan.com/api?module=account&action=txlistinternal&txhash={txhash}&apikey={token}"
get_token_tx = "https://api.bscscan.com/api?module=account&action=tokentx&address={addr}&endblock=99999999&apikey={token}&sort={sort}"
get_price_history = "https://web-api.coinmarketcap.com/v1/cryptocurrency/ohlcv/historical?id=8387&convert=USD&time_start=1602979200&time_end=1613606400"
#"https://api.bscscan.com/api?module=account&action=tokentx&contractaddress={contractaddr}&address={addr}&page=1&offset=0&sort=asc&apikey={token}}" 
#"https://api.bscscan.com/api?module=account&action=tokentx&address={addr}&endblock=99999999&apikey={token}"
cmc_key = "dbd5d894-d553-4895-8f99-b10ba96afc19"
cc_key = "2543955236ed985c9ae6038e5cb36a8ae2c60ab19ee91707d5d7270befac559b"
addr = "0xf58CbA27c683bC918566CBAC888D3Fab5BF076A0"
#addr = "0xF7B9BA7eB8E7542DD71825f695cE01f5F1D7b7df"

cmc_web_cookie_key = "dbe0c06eca475d6e835b61880a4f57a491613926595"
cmc_BSC_platform_id = 1839
cmc_ETH_platform_id = 1027 

binance_api_key = "MWmspj1MYWEhSVUyjAqGAGKTfzGCwAHDEnTjQ7lr05xQES1et1tCpYExk3aCXt79"
binance_secret_key = "fkvVecWUY56yome2lMZsQn65eZozC2F88pyoTEuZuQmC6ens88oOVhMQUQoTxmIg"
binance_api_url = "https://api.binance.com"m

gecko_ETH_platform_id = "ethereum"
gecko_BSC_platform_id = "binance-smart-chain"


##https://api.thegraph.com/subgraphs/name/pancakeswap/pairs
pcs_subgraph_url = "https://api.thegraph.com/subgraphs/name/pancakeswap/exchange"

venus_api_key = "nothingfornow"

beefy_pools_info_url = "https://raw.githubusercontent.com/beefyfinance/beefy-app/prod/src/features/configure/pools.js"

autofarm_info_url = "https://api.autofarm.network//bsc/get_farms_data"

warnings = {
    "001" : "Symbol not found in {0} but found in ETH chain"
}


WEI_DECIMALS = 18
GWEI_DECIMALS = 9
token_info_filename= "tokeninfo.dat"