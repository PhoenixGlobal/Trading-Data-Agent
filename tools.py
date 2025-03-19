import requests
import time
import json
import os
from log import log
from dotenv import load_dotenv
import re
import datetime

load_dotenv()


the_token = os.environ.get("TOKEN")


def get_coin_now_price(crypto_symbol: str):
    """Query the current price of a cryptocurrency (priced in USD). Enter the cryptocurrency symbol, such as BTC, ETH, or SOL.

    Args:
        crypto_symbol: the cryptocurrency symbol, such as BTC, ETH, or SOL.
    """

    crypto_id = crypto_symbol.upper()
    timestamp = int((time.time() - 5) * 1000)
    timestamp_str = str(timestamp)

    headers = {
        "accept": "application/json",
        "Token": the_token
    }
    params = {
        "symbol": crypto_id,
        "time": timestamp_str
    }
    url = 'https://phoenix.global/agent/api/crypto/symbolPrice'
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            log(f"The current price of {crypto_id} is {data['price']}.")
            return f"The current price of {crypto_id} is {data['price']}."
        else:
            log(f"Failed to retrieve {crypto_id} price.")
            return f"Failed to retrieve {crypto_id} price."
    except:
        log(f"Failed to retrieve {crypto_id} price.")
        return f"Failed to retrieve {crypto_id} price."


def match_specific_date(date_str):
    # （YYYY-MM-DD）
    date_pattern = r"\d{4}-\d{2}-\d{2}"

    if re.match(date_pattern, date_str):
        return True
    return False

def get_coin_historical_price(crypto_symbol: str, time_str: str, date_str: str):
    """Get the historical price of a cryptocurrency at a specific moment in time.

    Args:
        crypto_symbol: the cryptocurrency symbol, such as BTC, ETH, or SOL.
        date_str: the date parameter, if a vague date is provided, such as yesterday, the day before yesterday, or the day before that, convert them into numbers like -1, -2, -3 respectively,if a specific date is provided, convert it into a specific date format like 2006-01-02.
        time_str:  Time parameter, and convert the time into a format like 15:04:05.
    """

    crypto_id = crypto_symbol.upper()
    log(f"The date_str is {date_str}.")
    if match_specific_date(date_str):
        date_time_str = date_str + " " + time_str
    else:
        now_time = datetime.datetime.now()
        end_time = now_time + datetime.timedelta(days=int(date_str))
        end_date = end_time.strftime('%Y-%m-%d')
        log(f"The end_time is {end_time}, the end_date is {end_date}.")
        date_time_str = end_date + " " + time_str

    timeArray = time.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(timeArray)
    timestamp_str = str(int(timestamp * 1000))
    headers = {
        "accept": "application/json",
        "Token": the_token
    }
    params = {
        "symbol": crypto_id,
        "time": timestamp_str
    }
    url = 'https://phoenix.global/agent/api/crypto/symbolPrice'
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            log(f"The price of {crypto_id} is {data['price']}.")
            return f"The price of {crypto_id} is {data['price']}."
        else:
            log(f"Failed to retrieve {crypto_id} price.")
            return f"Failed to retrieve {crypto_id} price."
    except:
        log(f"Failed to retrieve {crypto_id} price.")
        return f"Failed to retrieve {crypto_id} price."


def get_coin_market_cap(crypto_symbol: str):
    """Get the market capitalization of a cryptocurrency.

    Args:
        crypto_symbol: the cryptocurrency symbol, such as BTC, ETH, or SOL.
    """

    crypto_id = crypto_symbol.upper()
    marketcap_url = "https://phoenix.global/agent/api/crypto/market-cap"
    headers = {
        "accept": "application/json",
        "Token": the_token
    }
    params = {
        "symbol": crypto_id
    }

    try:
        response = requests.get(marketcap_url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            log(f"The currentMarketCap of {crypto_id} is {data['currentMarketCap']},the fullyDilutedCap of {crypto_id} is {data['fullyDilutedCap']}")
            return f"The currentMarketCap of {crypto_id} is {data['currentMarketCap']},the fullyDilutedCap of {crypto_id} is {data['fullyDilutedCap']}"
        else:
            log(f"Failed to retrieve the market capitalization of {crypto_id}.")
            return f"Failed to retrieve the market capitalization of {crypto_id}."
    except:
        log(f"Failed to retrieve the market capitalization of {crypto_id}.")
        return f"Failed to retrieve the market capitalization of {crypto_id}."


def get_coin_supply_info(crypto_symbol: str):
    """Get the supply info of a cryptocurrency.

    Args:
        crypto_symbol: the cryptocurrency symbol, such as BTC, ETH, or SOL.
    """

    crypto_id = crypto_symbol.upper()
    supply_info_url = "https://phoenix.global/agent/api/crypto/supply-info"
    headers = {
        "accept": "application/json",
        "Token": the_token
    }
    params = {
        "symbol": crypto_id
    }

    try:
        response = requests.get(supply_info_url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            log(
                f"The circulatingSupply of {crypto_id} is {data['circulatingSupply']},the totalSupply of {crypto_id} is {data['totalSupply']},the maxSupply of {crypto_id} is {data['maxSupply']}")
            return f"The circulatingSupply of {crypto_id} is {data['circulatingSupply']},the totalSupply of {crypto_id} is {data['totalSupply']},the maxSupply of {crypto_id} is {data['maxSupply']}"
        else:
            log(f"Failed to retrieve the supply info of {crypto_id}.")
            return f"Failed to retrieve the supply info of {crypto_id}."
    except:
        log(f"Failed to retrieve the supply info of {crypto_id}.")
        return f"Failed to retrieve the supply info of {crypto_id}."


def get_coin_historical_periods_price(crypto_symbol: str, time_window: str):
    """Get the price and trading volume of a cryptocurrency for the past 7 days, past 30 days, or past 24 hours.

    Args:
        crypto_symbol: the cryptocurrency symbol, such as BTC, ETH, or SOL.
        time_window: Time window can only be one of the following: past 7 days, past 30 days, or past 24 hours, and retrieve the corresponding number 7, 30, or 24.
    """

    crypto_id = crypto_symbol.upper()
    historical_price_url = "https://phoenix.global/agent/api/crypto/historical-price"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    params = {
        "symbol": crypto_id,
        "timeDimension": int(time_window)
    }
    try:
        response = requests.get(historical_price_url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            price_datas = []
            for dat in data["klineDatas"]:
                price_data = {
                    "price": dat["Price"],
                    "volume": dat["Volume"],
                    "time": dat["Time"],
                }
                price_datas.append(price_data)
            json_arr = json.dumps(price_datas)
            log(f"The price and trading volume of {crypto_id} is {json_arr}.")
            return f"The price and trading volume of {crypto_id} is {json_arr}."
        else:
            return f"Failed to retrieve the price and trading volume of {crypto_id}."
    except:
        log(f"Failed to retrieve the price and trading volume of {crypto_id}.")
        return f"Failed to retrieve the price and trading volume of {crypto_id}."


def get_coin_order_book(crypto_symbol: str):
    """Get the order book of a cryptocurrency.

    Args:
        crypto_symbol: the cryptocurrency symbol, such as BTC, ETH, or SOL.
    """

    crypto_id = crypto_symbol.upper()
    orderbook_url = "https://phoenix.global/agent/api/crypto/order-book"
    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    params = {
        "symbol": crypto_id,
    }

    try:
        response = requests.get(orderbook_url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            json_ask_arr = json.dumps(data['asks'])
            json_bid_arr = json.dumps(data['bids'])
            log(f"The ask order book of {crypto_id} is {json_ask_arr},the bid order book of {crypto_id} is {json_bid_arr}")
            return f"The ask order book of {crypto_id} is {json_ask_arr},the bid order book of {crypto_id} is {json_bid_arr}"
        else:
            log(f"Failed to retrieve the order book of {crypto_id}.")
            return f"Failed to retrieve the order book of {crypto_id}."
    except:
        log(f"Failed to retrieve the order book of {crypto_id}.")
        return f"Failed to retrieve the order book of {crypto_id}."


def get_coin_rsi(crypto_symbol: str, time_span: str, time_window: str):
    """Get the RSI indicator of a cryptocurrency over a period measured in hours or days.

    Args:
        crypto_symbol: the cryptocurrency symbol, such as BTC, ETH, or SOL.
        time_span: The time span,it can only be day or hour. When specifying multiple days or hours, the time span parameter should be "day" and "hour" respectively.
        time_window: The time window parameter can only be a numeric value, representing a certain number of days or hours, and it works together with the time_span parameter. For example, if the duration is in hours or days, the time window parameter is a numerical value, while the time_span parameter specifies "hour" or "day".

    """

    crypto_id = crypto_symbol.upper()
    rsi_url = "https://phoenix.global/agent/api/crypto/rsi"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    log(f"The time_span is {time_span}, the time_window is {time_window}")
    params = {
        "symbol": crypto_id,
        "timespan": time_span,
        "timeWindow": time_window
    }
    try:
        response = requests.get(rsi_url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            rsi_datas = []
            for dat in data["rsiData"]:
                rsi_data = {
                    "time": dat["Time"],
                    "value": dat["Value"],
                }
                rsi_datas.append(rsi_data)
            json_arr = json.dumps(rsi_datas)
            log(f"The RSI indicator of {crypto_id} is {json_arr}.")
            return f"The RSI indicator of {crypto_id} is {json_arr}."
        else:
            return f"Failed to retrieve the RSI indicator of {crypto_id}."
    except:
        log(f"Failed to retrieve the RSI indicator of {crypto_id}.")
        return f"Failed to retrieve the RSI indicator of {crypto_id}."

def get_holders(crypto_symbol: str, limit: str):
    """Get holders of a cryptocurrency.For example, get the top 100 holders. Only token holders can be queried; mainchain coins cannot be queried. For example, you can retrieve the top 100 holders of SHIB, but not the top 100 holders of BTC.

    Args:
        crypto_symbol: the cryptocurrency symbol, such as SHIB, PEPE, or BONK.
        limit: The limit parameter represents the quantity. For example, when retrieving the top 100 holders, the limit is set to 100. The maximum limit cannot exceed 200; if it exceeds 200, it will still be set to 200.

    """

    crypto_id = crypto_symbol.upper()
    rsi_url = "https://phoenix.global/agent/api/crypto/holders"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    log(f"The crypto_symbol is {crypto_symbol}, the limit is {limit}")
    params = {
        "symbol": crypto_id,
        "limit": limit
    }
    try:
        response = requests.get(rsi_url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            holder_datas = []
            amount = len(data["holdersData"])
            for dat in data["holdersData"]:
                holder_data = {
                    "holderAddress": dat["holderAddress"],
                    "amount": dat["amount"],
                    "rank": dat["rank"],
                }
                holder_datas.append(holder_data)
            json_arr = json.dumps(holder_datas)
            log(f"The top {amount} holders of {crypto_id} are {json_arr}.")
            return f"The top {amount} holders of {crypto_id} are {json_arr}."
        else:
            return f"Failed to retrieve the holders of {crypto_id}."
    except:
        log(f"Failed to retrieve the holders of {crypto_id}.")
        return f"Failed to retrieve the holders of {crypto_id}."

def get_contract_holders(contract_address: str, limit: str):
    """Get holders of a cryptocurrency based on the contract address.For example, get the top 100 holders.

    Args:
        contract_address: The contract address of a cryptocurrency.For example, SHIB's contract address is 0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce. Another example is WIF's contract address, which is EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm.
        limit: The limit parameter represents the quantity. For example, when retrieving the top 100 holders, the limit is set to 100. The maximum limit cannot exceed 200; if it exceeds 200, it will still be set to 200.

    """

    rsi_url = "https://phoenix.global/agent/api/crypto/addressHolders"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    log(f"The contract_address is {contract_address}, the limit is {limit}")
    params = {
        "address": contract_address,
        "limit": limit
    }
    try:
        response = requests.get(rsi_url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            holder_datas = []
            amount = len(data["holdersData"])
            for dat in data["holdersData"]:
                holder_data = {
                    "holderAddress": dat["holderAddress"],
                    "amount": dat["amount"],
                    "rank": dat["rank"],
                }
                holder_datas.append(holder_data)
            json_arr = json.dumps(holder_datas)
            log(f"The top {amount} holders of {contract_address} are {json_arr}.")
            return f"The top {amount} holders of {contract_address} are {json_arr}."
        else:
            return f"Failed to retrieve the holders of {contract_address}."
    except:
        log(f"Failed to retrieve the holders of {contract_address}.")
        return f"Failed to retrieve the holders of {contract_address}."

def get_contract_token_info(contract_address: str):
    """Get the token information based on its contract address and return details such as the token's name, symbol, total supply, market capitalization, price, etc.

    Args:
        contract_address: The contract address of a cryptocurrency.For example, SHIB's contract address is 0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce. Another example is WIF's contract address, which is EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm.

    """

    rsi_url = "https://phoenix.global/agent/api/crypto/tokenInfoByAddress"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    log(f"The contract_address is {contract_address}.")
    params = {
        "address": contract_address
    }
    try:
        response = requests.get(rsi_url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            json_arr = json.dumps(data["tokenData"])
            log(f"The token information of {contract_address} is {json_arr}.")
            return f"The token information of {contract_address} is {json_arr}."
        else:
            return f"Failed to retrieve the token information of {contract_address}."
    except:
        log(f"Failed to retrieve the token information of {contract_address}.")
        return f"Failed to retrieve the token information of {contract_address}."