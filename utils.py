import os
import json
from loguru import logger
from dotenv import load_dotenv
from datetime import datetime
import requests

import okx.Account as Account
import okx.MarketData as Market
import okx.Trade as Trade

def setup_okx_client()-> Account.AccountAPI:
    load_dotenv() 
    OKX_APIKEY = os.getenv('OKX_APIKEY')
    OKX_SECRET = os.getenv('OKX_SECRET')
    OKX_PASSPHRASE = os.getenv('OKX_PASSPHRASE')
    FLAG = json.load(open('/home/jupiter_arbitrage/config.json', 'r')).get('okx_flag', '1')
    accountAPI = Account.AccountAPI(api_key=OKX_APIKEY, 
                                    api_secret_key=OKX_SECRET, 
                                    passphrase=OKX_PASSPHRASE, 
                                    flag=FLAG)
    marketDataAPI = Market.MarketAPI(flag=FLAG)
    tradeAPI = Trade.TradeAPI(api_key=OKX_APIKEY, 
                              api_secret_key=OKX_SECRET, 
                              passphrase=OKX_PASSPHRASE, 
                              flag=FLAG)
    return accountAPI, marketDataAPI, tradeAPI


def fetch_today_okx_price(symbol:str, marketDataAPI: Market.MarketAPI) -> float:
    """從 OKX 獲取指定交易對的今日價格"""
    res = marketDataAPI.get_ticker(instId=symbol)
    price = res['data'][0]['last']
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
    address = json.load(open('/home/jupiter-arbitrage/config.json', 'r')).get('metamask_address')
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


def fetch_okx_positions_size(accountAPI: Account.AccountAPI)-> dict:
    res = accountAPI.get_positions(instType='SWAP')['data']
    okx_positions_size_metrics = {
        'BTC': 0.0, 
        'ETH': 0.0, 
        'SOL': 0.0
    }
    for position in res:
        if position['instId'] == 'BTC-USDT-SWAP':
            okx_positions_size_metrics['BTC'] += float(position['pos']) * 0.01
        elif position['instId'] == 'ETH-USDT-SWAP':
            okx_positions_size_metrics['ETH'] += float(position['pos']) * 0.1
        elif position['instId'] == 'SOL-USDT-SWAP':
            okx_positions_size_metrics['SOL'] += float(position['pos'])
    
    return okx_positions_size_metrics


def place_order(contract: str, size: float, tradeAPI: Trade.TradeAPI):
    """ 在 OKX 創建訂單"""
    contract_qty_map = {
        'BTC-USDT-SWAP': 0.01,
        'ETH-USDT-SWAP': 0.01,
        'SOL-USDT-SWAP': 0.01
    }
    res = tradeAPI.place_order(
        instId=contract, 
        tdMode='cross', 
        side='buy' if size > 0 else 'sell', 
        ordType='market', 
        sz=abs(size) * contract_qty_map[contract]
    )
    if res['code'] == '0':
        order_id = res['data'][0]['ordId']
    else:
        logger.error(f"訂單創建失敗: {res['msg']}")
        return None
    order_details = tradeAPI.get_order(ordId=order_id, instId=contract)['data'][0]

    trade = {
        'contract': order_details['instId'], 
        'size': float(order_details['fillSz']) * contract_qty_map[contract] * (10 if 'ETH' in contract else 100 if 'SOL' in contract else 1), 
        'price': order_details['avgPx'], 
        'status': order_details['state'],
        'created_at': datetime.fromtimestamp(int(order_details['cTime']) / 1000).strftime('%Y-%m-%d %H:%M:%S')
    }
    return trade


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
        print("Message sent successfully")
    else:
        print(f"Failed sending message: {response.json().get('description', '未知錯誤')}")


def margin_call_check(accountAPI: Account.AccountAPI) -> float:
    """
    檢查 OKX 帳戶是否有保證金通知。
    """
    res = accountAPI.get_positions(instType='SWAP')['data']
    for position in res:
        if float(position['mgnRatio']) < 2.0:
            logger.warning(f"保證金通知: {position['instId']} 的保證金率低於 1.0")
            return f"🆘保證金通知: {float(position['instId']): .2f} 的保證金率低於 2.0"
        else: 
            logger.info("所有持倉的保證金率均正常")
            return f"✅保證金充足，當前保證金率: {float(position['mgnRatio']): .2f}"
