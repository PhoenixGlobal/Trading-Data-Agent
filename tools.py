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
    """Get holders of a cryptocurrency.For example, get the top 100 holders. Currently, querying holders of tokens on the Solana chain is not supported.

    Args:
        crypto_symbol: the cryptocurrency symbol, such as SHIB, PEPE, or BONK.
        limit: The limit parameter represents the quantity. For example, when retrieving the top 100 holders, the limit is set to 100. The maximum limit cannot exceed 200; if it exceeds 200, it will still be set to 200.

    """

    crypto_id = crypto_symbol.upper()
    url = "https://phoenix.global/agent/api/crypto/holders"

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
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            holder_datas = []
            amount = len(data["holdersData"])
            for dat in data["holdersData"]:
                holder_data = {
                    "holderAddress": dat["holderAddress"],
                    "amount": dat["amount"],
                    "rank": dat["rank"],
                    "valueUsd": dat["valueUsd"],
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
    """Get holders of a cryptocurrency based on the contract address.For example, get the top 100 holders. Currently, querying holders of tokens on the Solana chain is not supported.

    Args:
        contract_address: The contract address of a cryptocurrency.For example, SHIB's contract address is 0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce.
        limit: The limit parameter represents the quantity. For example, when retrieving the top 100 holders, the limit is set to 100. The maximum limit cannot exceed 200; if it exceeds 200, it will still be set to 200.

    """

    url = "https://phoenix.global/agent/api/crypto/addressHolders"

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
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            holder_datas = []
            amount = len(data["holdersData"])
            for dat in data["holdersData"]:
                holder_data = {
                    "holderAddress": dat["holderAddress"],
                    "amount": dat["amount"],
                    "rank": dat["rank"],
                    "valueUsd": dat["valueUsd"],
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
    """Get the token information based on its contract address and return details such as the token's name, symbol, precision(decimals), protocol type(token standard, such as ERC-20), total number of holders, total supply, circulating supply, market capitalization, price, etc.

    Args:
        contract_address: The contract address of a cryptocurrency.For example, SHIB's contract address is 0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce. Another example is WIF's contract address, which is EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm.

    """

    url = "https://phoenix.global/agent/api/crypto/tokenInfoByAddress"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    log(f"The contract_address is {contract_address}.")
    params = {
        "address": contract_address
    }
    try:
        response = requests.get(url, headers=headers, params=params)
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

def get_coin_info(crypto_symbol: str):
    """Get a cryptocurrency's information based on its symbol and return details such as the cryptocurrency's name, description, contract address, and the blockchain it is on. Some cryptocurrencies may have multiple contract addresses on different blockchains.

    Args:
        crypto_symbol: the cryptocurrency symbol, such as BTC, ETH, or SOL.
    """

    crypto_id = crypto_symbol.upper()
    url = "https://phoenix.global/agent/api/crypto/coinInfo"
    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    params = {
        "symbol": crypto_id,
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            json_arr = json.dumps(data["coinData"])
            log(f"The information of {crypto_id} is {json_arr}.")
            return f"The information of {crypto_id} is {json_arr}."
        else:
            log(f"Failed to retrieve the information of {crypto_id}.")
            return f"Failed to retrieve the information of {crypto_id}."
    except:
        log(f"Failed to retrieve the information of {crypto_id}.")
        return f"Failed to retrieve the information of {crypto_id}."

def get_dex_pool_info(contract_address: str):
    """Get DEX pool information based on the token's contract address and return details about DEX pool pairs, such as the blockchain it is on, URL, pair contract address, the two tokens in the pair, price, number of trades (buy and sell counts), trading volume, price changes, liquidity (amount of tokens in the pool and their USD value), FDV, and other relevant data. Multiple pairs may be returned.

    Args:
        contract_address: The contract address of a cryptocurrency.For example, SHIB's contract address is 0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce. Another example is WIF's contract address, which is EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm.

    """

    url = "https://phoenix.global/agent/api/crypto/dexPoolInfo"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    log(f"The contract_address is {contract_address}.")
    params = {
        "address": contract_address
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            json_arr = json.dumps(data["dexPairs"])
            log(f"The DEX pool pairs information of {contract_address} are {json_arr}.")
            return f"The DEX pool pairs information of {contract_address} are {json_arr}."
        else:
            return f"Failed to retrieve the DEX pool pairs information of {contract_address}."
    except:
        log(f"Failed to retrieve the DEX pool pairs information of {contract_address}.")
        return f"Failed to retrieve the DEX pool pairs information of {contract_address}."

def get_address_summary(address: str, chain_name: str):
    """Get an overview of a specific address, returning whether it is a contract address, whether it is a token (if so, return the token's symbol), the symbol (balanceSymbol) and balance (balance) of the native currency on the chain, the total number of transactions (transactionCount), the total amount of balanceSymbol sent (sendAmount), the total amount of balanceSymbol received (receiveAmount), the total number of different token types held (tokenAmount), and the total value of these tokens in terms of balanceSymbol (totalTokenValue).

    Args:
        address: Blockchain address, such as 0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce.
        chain_name:The short name of the chain can only be one of the following values: btc, eth, bsc, solana, etc, dash, op, bch, tron, ltc, avaxc, apt, polygon, doge, arbitrum, kaia, zksync, sui, ronin, opbnb, base, ftm, cosmos, kava. Other chains are not supported. The chain name should be converted to its corresponding abbreviation, such as converting BNB Chain to bsc, Ethereum to eth, Bitcoin to btc, Solana to solana, Avalanche to avaxc, and BASE to base.

    """

    url = "https://phoenix.global/agent/api/crypto/addressSummary"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    log(f"The address is {address}.")
    params = {
        "address": address,
        "chainShortName": chain_name
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            json_arr = json.dumps(data["summary"])
            log(f"The summary information of {address} are {json_arr}.")
            return f"The summary information of {address} are {json_arr}."
        else:
            return f"Failed to retrieve the summary information of {address}."
    except:
        log(f"Failed to retrieve the summary information of {address}.")
        return f"Failed to retrieve the summary information of {address}."

def get_address_tokens(address: str, chain_name: str):
    """Query which tokens a specific blockchain address holds and return the token symbol, contract address, balance, token price, and token value (in USD). A maximum of 50 tokens will be returned, even if the address holds more than 50 tokens.

    Args:
        address: Blockchain address, such as 0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce.
        chain_name:The short name of the chain can only be one of the following values: btc, eth, bsc, solana, etc, dash, op, bch, tron, ltc, avaxc, apt, polygon, doge, arbitrum, kaia, zksync, sui, ronin, opbnb, base, ftm, cosmos, kava. Other chains are not supported. The chain name should be converted to its corresponding abbreviation, such as converting BNB Chain to bsc, Ethereum to eth, Bitcoin to btc, Solana to solana, Avalanche to avaxc, and BASE to base.

    """

    url = "https://phoenix.global/agent/api/crypto/addressTokens"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    log(f"The address is {address}.")
    params = {
        "address": address,
        "chainShortName": chain_name
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            json_arr = json.dumps(data["tokenList"])
            log(f"The token list of {address} are {json_arr}.")
            return f"The token list of {address} are {json_arr}."
        else:
            return f"Failed to retrieve the token list of {address}."
    except:
        log(f"Failed to retrieve the token list of {address}.")
        return f"Failed to retrieve the token list of {address}."

def get_address_token(address: str, chain_name: str,token_contract_address: str):
    """Query the holdings of a specific blockchain address for a specific token. The token's contract address is required—if only the token symbol is provided, call the get_coin_info method to retrieve the contract address based on the symbol first. Return the token symbol, contract address, balance, token price, and token value (in USD).

    Args:
        address: Blockchain address, such as 0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce.
        chain_name:The short name of the chain can only be one of the following values: btc, eth, bsc, solana, etc, dash, op, bch, tron, ltc, avaxc, apt, polygon, doge, arbitrum, kaia, zksync, sui, ronin, opbnb, base, ftm, cosmos, kava. Other chains are not supported. The chain name should be converted to its corresponding abbreviation, such as converting BNB Chain to bsc, Ethereum to eth, Bitcoin to btc, Solana to solana, Avalanche to avaxc, and BASE to base.
        token_contract_address: The contract address of a token.For example, SHIB's contract address is 0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce.

    """

    url = "https://phoenix.global/agent/api/crypto/addressToken"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    log(f"The address is {address}, the token_contract_address is {token_contract_address}.")
    params = {
        "address": address,
        "chainShortName": chain_name,
        "tokenContractAddress": token_contract_address
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            json_arr = json.dumps(data["tokenList"])
            log(f"The holdings of address {address} for token {token_contract_address} are are {json_arr}.")
            return f"The holdings of address {address} for token {token_contract_address} are are {json_arr}."
        else:
            return f"Failed to retrieve the holdings of address {address} for token {token_contract_address}."
    except:
        log(f"Failed to retrieve the holdings of address {address} for token {token_contract_address}.")
        return f"Failed to retrieve the holdings of address {address} for token {token_contract_address}."

def get_coin_historical_price_change(crypto_symbol: str):
    """Get the percentage price change of a cryptocurrency over the past 24 hours, 7 days, and 30 days.

    Args:
        crypto_symbol: the cryptocurrency symbol, such as BTC, ETH, or SOL.

    """

    crypto_id = crypto_symbol.upper()
    url = "https://phoenix.global/agent/api/crypto/priceChange"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    params = {
        "symbol": crypto_id
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            json_arr = json.dumps(data['priceChangeData'])
            log(f"The percentage price change of {crypto_id} is {json_arr}.")
            return f"The percentage price change of {crypto_id} is {json_arr}."
        else:
            return f"Failed to retrieve the percentage price change of {crypto_id}."
    except:
        log(f"Failed to retrieve the percentage price change of {crypto_id}.")
        return f"Failed to retrieve the percentage price change of {crypto_id}."


def get_coin_macd(crypto_symbol: str, days: str):
    """Get the MACD indicator of a cryptocurrency over a period measured in days.

    Args:
        crypto_symbol: the cryptocurrency symbol, such as BTC, ETH, or SOL.
        days: indicates the number of days; defaults to 30 if left empty.

    """

    crypto_id = crypto_symbol.upper()
    url = "https://phoenix.global/agent/api/crypto/macd"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    log(f"The days is {days}.")
    params = {
        "symbol": crypto_id,
        "days": days
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            json_arr = json.dumps(data["macdData"])
            log(f"The MACD indicator of {crypto_id} is {json_arr}.")
            return f"The MACD indicator of {crypto_id} is {json_arr}."
        else:
            return f"Failed to retrieve the MACD indicator of {crypto_id}."
    except:
        log(f"Failed to retrieve the MACD indicator of {crypto_id}.")
        return f"Failed to retrieve the MACD indicator of {crypto_id}."


def get_coin_kdj(crypto_symbol: str, days: str):
    """Get the KDJ indicator of a cryptocurrency over a period measured in days.

    Args:
        crypto_symbol: the cryptocurrency symbol, such as BTC, ETH, or SOL.
        days: indicates the number of days; defaults to 30 if left empty.

    """

    crypto_id = crypto_symbol.upper()
    url = "https://phoenix.global/agent/api/crypto/kdj"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    log(f"The days is {days}.")
    params = {
        "symbol": crypto_id,
        "days": days
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            json_arr = json.dumps(data["kdjData"])
            log(f"The KDJ indicator of {crypto_id} is {json_arr}.")
            return f"The KDJ indicator of {crypto_id} is {json_arr}."
        else:
            return f"Failed to retrieve the KDJ indicator of {crypto_id}."
    except:
        log(f"Failed to retrieve the KDJ indicator of {crypto_id}.")
        return f"Failed to retrieve the KDJ indicator of {crypto_id}."


def get_tokens_by_topic(topic: str):
    """Get a list of popular tokens based on the topic. The valid values for the topic are: hot, meme, gainer, solana, new, bsc, loser, eth, base, depin, ai, l2, gamefi, rwa, arbitrum, blast, polygon, optimism, avalanche, merlin, BSC-Meme-Boost. If the topic is any other value, it must first be converted to one of these valid values.

    Args:
        topic: Currently trending topics, such as meme and AI.

    """

    url = "https://phoenix.global/agent/api/crypto/getTokenListByTopic"

    headers = {
        "accept": "application/json",
        "Token": the_token
    }

    log(f"The topic is {topic}.")
    params = {
        "topic": topic
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        if data['code'] == 200:
            json_arr = json.dumps(data["data"])
            log(f"The popular tokens based on the topic of {topic} are {json_arr}.")
            return f"The popular tokens based on the topic of {topic} are {json_arr}."
        else:
            return f"Failed to retrieve the popular tokens based on the topic of {topic}."
    except:
        log(f"Failed to retrieve the popular tokens based on the topic of {topic}.")
        return f"Failed to retrieve the popular tokens based on the topic of {topic}."