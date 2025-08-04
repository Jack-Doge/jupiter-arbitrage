import os
import json
from loguru import logger
from dotenv import load_dotenv
import time
import requests
import pandas as pd
import numpy as np

import gate_api

import json
import os
import gate_api
from dotenv import load_dotenv

def setup_gate_client()-> gate_api.FuturesApi:
    """設定 Gate.io API 客戶端並處理身份驗證"""
    load_dotenv() 
    GATE_APIKEY = os.getenv('GATE_APIKEY')
    GATE_SECRET = os.getenv('GATE_SECRET')

    configuration = gate_api.Configuration(
        host=json.load(open('config.json', 'r')).get('gate_host_live'), 
        key=GATE_APIKEY,
        secret=GATE_SECRET
    )
    api_client = gate_api.ApiClient(configuration)
    api_instance = gate_api.FuturesApi(api_client)
    return api_instance


def fetch_today_gate_price(symbol, api_instance) -> float:
    """從 Gate.io 獲取指定交易對的今日價格"""
    res = api_instance.list_futures_tickers(settle=symbol.split('_')[1].lower(), 
                                            contract=symbol
                                            )
    price = res[0].last
    return float(price)
    

def fetch_jlp_price()-> float:
    url = "https://lite-api.jup.ag/price/v2"
    ids_to_query = "27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4"
    params = {
        "ids": ids_to_query
    }
    payload = {}
    headers = {
    'Accept': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload, params=params).json()
    price = response['data'][ids_to_query]['price']
    return float(price)


def fetch_metamask_balance()-> dict:
    """獲取指定地址的 MetaMask 餘額"""
    address = json.load(open('config.json', 'r')).get('metamask_address')
    url = f"https://lite-api.jup.ag/ultra/v1/balances/{address}"
    payload = {}
    headers = {
    'content-type': 'application/json'
    }
    response = requests.request("GET", url, headers=headers, data=payload).json()
    balance_metrics = {
        'JLP': response['27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4']['uiAmount'], 
        'GAS': response['SOL']['uiAmount'],
    }
    return balance_metrics


def fetch_gate_positions_size(api_instance)-> dict:
    res = api_instance.list_positions(settle='usdt', holding=True, limit=10)
    gate_positions_size_metrics = {
        'BTC': 0.0, 
        'ETH': 0.0, 
        'SOL': 0.00
    }
    for position in res:
        if position.contract == 'BTC_USDT':
            gate_positions_size_metrics['BTC'] += position.size * 0.0001
        elif position.contract == 'ETH_USDT':
            gate_positions_size_metrics['ETH'] += position.size * 0.01
        elif position.contract == 'SOL_USDT':
            gate_positions_size_metrics['SOL'] += position.size

    return gate_positions_size_metrics


def place_order(contract: str, size: float, api_instance: gate_api.FuturesApi):
    """ 在 Gate.io 創建訂單"""
    contract_qty_map = {
        'BTC_USDT': 0.0001,
        'ETH_USDT': 0.01,
        'SOL_USDT': 1.0
    }
    futures_order = gate_api.FuturesOrder(
        contract=contract,
        size= int(size / contract_qty_map[contract]), 
        price='0', 
        tif='ioc'
    )
    res = api_instance.create_futures_order(settle='usdt', futures_order=futures_order)
    trade = {
        'contract': res.contract, # type: ignore
        'size': res.size * contract_qty_map[res.contract], # type: ignore
        'price': res.fill_price, # type: ignore
        'status': res.status, # type: ignore
        'created_at': res.create_time # type: ignore
    }
    return trade

place_order(contract='BTC_USDT', size=-0.0001, api_instance=setup_gate_client())


def setup_telegram_bot()-> tuple:
    load_dotenv()
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    return TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram_message(bot_token, chat_id, message: str):
    """
    發送訊息到 Telegram。
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, json=payload)

    if response.json().get('ok'):
        logger.success("訊息發送成功！")
    else:
        logger.error(f"訊息發送失敗: {response.json().get('description', '未知錯誤')}")



if __name__ == "__main__":
    # FETCH_GATE_PRICE
    # api_instance = setup_gate_client()

    # price_metrics = {
    #     'btc_price': fetch_today_gate_price('BTC_USDT', api_instance),
    #     'eth_price': fetch_today_gate_price('ETH_USDT', api_instance),
    #     'sol_price': fetch_today_gate_price('SOL_USDT', api_instance),
    #     'jlp_price': fetch_jlp_price(),
    # }
    
    # bot_token, chat_id = setup_telegram_bot()
    # message = "Hello, this is a test message from Jupiter Arbitrage Bot!"
    # send_telegram_message(bot_token, chat_id, message)
    pass