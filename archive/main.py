import json
from loguru import logger
import pandas as pd
import numpy as np

from utils import (
    setup_gate_client, 
    send_telegram_message,
    setup_telegram_bot,
    fetch_today_gate_price,
    fetch_gate_positions_size, 
    fetch_jlp_price,
    fetch_metamask_balance, 
    place_order
)

class JupiterGateArbitrageRebalance:
    def __init__(self):
        self.api_instance = setup_gate_client()
        self.tg_bot_token, self.tg_chat_id = setup_telegram_bot()
        self.target_weights = json.load(open('config.json', 'r')).get('target_weights', {})
        # price metrics
        self.btc_price: float
        self.eth_price: float
        self.sol_price: float
        self.jlp_price: float
        # quantity metrics
        self.btc_qty: float
        self.eth_qty: float
        self.sol_qty: float
        self.jlp_qty: float
        # value metrics
        self.btc_value: float
        self.eth_value: float
        self.sol_value: float
        self.jlp_value: float
        # weights metrics
        self.btc_weight: float
        self.eth_weight: float
        self.sol_weight: float
        self.jlp_weight: float
        # portfolio metrics
        self.portfolio_value: float
        # others
        self.gas_qty: float


    def fetch_data(self):
        # price
        self.btc_price = fetch_today_gate_price('BTC_USDT', self.api_instance)
        self.eth_price = fetch_today_gate_price('ETH_USDT', self.api_instance)
        self.sol_price = fetch_today_gate_price('SOL_USDT', self.api_instance)
        self.jlp_price = fetch_jlp_price()
        # quantity
        metamask_positions_metrics = fetch_metamask_balance()
        gate_positions_metrics = fetch_gate_positions_size(self.api_instance)  
        self.btc_qty = gate_positions_metrics['BTC']
        self.eth_qty = gate_positions_metrics['ETH']
        self.sol_qty = gate_positions_metrics['SOL']
        self.jlp_qty = metamask_positions_metrics['JLP']
        self.gas_qty = metamask_positions_metrics['GAS']
        # value 
        self.btc_value = self.btc_price * self.btc_qty
        self.eth_value = self.eth_price * self.eth_qty
        self.sol_value = self.sol_price * self.sol_qty
        self.jlp_value = self.jlp_price * self.jlp_qty
        # portfolio value
        self.portfolio_value = self.btc_value + self.eth_value + self.sol_value + self.jlp_value
        # weights
        self.btc_weight = self.btc_value / self.portfolio_value
        self.eth_weight = self.eth_value / self.portfolio_value
        self.sol_weight = self.sol_value / self.portfolio_value
        self.jlp_weight = self.jlp_value / self.portfolio_value


    def rebalance(self):
        """執行資產再平衡"""
        # 1. 獲取當前價格和餘額
        self.fetch_data()

        # 2. 計算需要調整的數量 (以JLP為基準，其他資產配合)
        adjustments = {}
        for asset, target_weight in self.target_weights.items():
            if asset == 'JLP':
                continue
            
            target_value = self.jlp_value * target_weight
            target_qty = target_value / getattr(self, f"{asset.lower()}_price")
            current_qty = getattr(self, f"{asset.lower()}_qty")
            adjustments[asset] = target_qty - current_qty
        
        # 3. 執行調整
        msg = '🔔JLP Arbitrage Rebalance Notify\n'
        for asset, adjustment in adjustments.items():
            if adjustment > 0:
                trade = place_order(f"{asset}_USDT", adjustment, self.api_instance)
                msg += f"買入 {trade['size']} {asset} \n"
            elif adjustment < 0:
                trade = place_order(f"{asset}_USDT", -adjustment, self.api_instance)
                msg += f"賣出 {trade['size']:.4f} {asset}\n"
            else:
                msg += f"{asset} 不需要調整\n"
        logger.info(f'執行調整\n {msg}')
        
        # 4. 發送Telegram通知
        send_telegram_message(self.tg_bot_token, self.tg_chat_id, msg)

if __name__ == "__main__":
    rebalance = JupiterGateArbitrageRebalance()
    rebalance.rebalance()