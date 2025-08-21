import json
import pandas as pd
import numpy as np

from utils import (
    setup_okx_client, 
    fetch_today_okx_price, 
    fetch_jlp_price, 
    fetch_metamask_balance, 
    fetch_okx_positions_size, 
    place_order, 
    margin_call_check, 
    setup_telegram_bot, 
    send_telegram_message, 
)

class JupiterOKXArbitrageRebalance:
    def __init__(self):
        self.accountAPI, self.marketDataAPI, self.tradeAPI = setup_okx_client() 
        self.tg_bot_token, self.tg_chat_id = setup_telegram_bot()
        self.target_weights = json.load(open('/home/jupiter-arbitrage/config.json', 'r')).get('target_weights', {})
        self.minimum_order_size = {
            'BTC': 0.0001,
            'ETH': 0.001,
            'SOL': 0.01
        }
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
        self.btc_price = fetch_today_okx_price('BTC-USDT-SWAP', self.marketDataAPI)
        self.eth_price = fetch_today_okx_price('ETH-USDT-SWAP', self.marketDataAPI)
        self.sol_price = fetch_today_okx_price('SOL-USDT-SWAP', self.marketDataAPI)
        self.jlp_price = fetch_jlp_price()
        # quantity
        metamask_positions_metrics = fetch_metamask_balance()
        gate_positions_metrics = fetch_okx_positions_size(self.accountAPI)  
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
        print(f'調整前資產配置:\n'
                f' - BTC {(self.btc_weight / self.jlp_weight) * 100: .2f}%\n' \
                f' - ETH {(self.eth_weight / self.jlp_weight) * 100: .2f}%\n' \
                f' - SOL {(self.sol_weight / self.jlp_weight) * 100: .2f}%')
                
        # 2. 計算需要調整的數量 (以JLP為基準，其他資產配合)
        adjustments = {}
        for asset, target_weight in self.target_weights.items():
            if asset == 'JLP':
                continue

            target_value = -(self.jlp_value * target_weight)
            target_qty = target_value / getattr(self, f"{asset.lower()}_price")
            current_qty = getattr(self, f"{asset.lower()}_qty")
            adjustments[asset] = int(round((target_qty - current_qty) / self.minimum_order_size.get(asset), 0))

        # 3. 執行調整
        msg = '🔔JLP Arbitrage Rebalance🔔\n'
        for asset, adjustment in adjustments.items():
            if adjustment > 0:
                trade = place_order(f"{asset}-USDT-SWAP", adjustment, self.tradeAPI)
                msg += f" - 買入 {trade['size']} {asset} \n"
            elif adjustment < 0:
                trade = place_order(f"{asset}-USDT-SWAP", adjustment, self.tradeAPI)
                msg += f" - 賣出 {trade['size']} {asset}\n"
            else:
                msg += f" - {asset} 不需要調整\n" 
        print(f'完成再平衡 \n {msg}')
        # 4. 更新權重
        self.fetch_data()
        msg += f'➡️調整後資產配置\n' \
                f' - BTC {(self.btc_weight / self.jlp_weight) * 100: .2f}%\n' \
                f' - ETH {(self.eth_weight / self.jlp_weight) * 100: .2f}%\n' \
                f' - SOL {(self.sol_weight / self.jlp_weight) * 100: .2f}%\n' \
                
        print(f'調整後資產配置:\n' \
                f' - BTC {(self.btc_weight / self.jlp_weight) * 100: .2f}%\n' \
                f' - ETH {(self.eth_weight / self.jlp_weight) * 100: .2f}%\n' \
                f' - SOL {(self.sol_weight / self.jlp_weight) * 100: .2f}%')

        # 5. 檢查保證金餘額
        msg += margin_call_check(self.accountAPI)

        # 6. 發送Telegram通知
        send_telegram_message(self.tg_bot_token, self.tg_chat_id, msg)

        # except Exception as e:
        #     print.error(f"發生錯誤: {e}")
        #     send_telegram_message(self.tg_bot_token, self.tg_chat_id, f"❗️發生錯誤: {e}")


if __name__ == "__main__":
    arbbot = JupiterOKXArbitrageRebalance()
    arbbot.rebalance()
