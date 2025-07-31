
import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# --- 前置作業 ---
# 1. 安裝必要的套件:
#    pip install requests pandas
#
# 2. 填寫您的 CoinMarketCap API Key:
#    註冊一個免費帳戶: https://pro.coinmarketcap.com/
#    然後將 API Key 填入下方變數。
#    注意：腳本預設使用沙盒(sandbox)環境，其數據為模擬資料。
#    若要使用真實數據，請將 USE_SANDBOX 設為 False，並使用生產環境的 API Key。

# --- 組態設定 ---
# CoinMarketCap API
load_dotenv()  # 從 .env 檔案讀取環境變數
CMC_API_KEY = os.getenv('CMC_API_KEY', 'YOUR_COINMARKETCAP_API_KEY')
USE_SANDBOX = True

# 幣安 API
BINANCE_API_URL = 'https://api.binance.com/api/v3/klines'

# --- 策略參數 ---
INITIAL_INVESTMENT = 1000.00
BACKTEST_START_DATE = '2024-07-01'

# JLP (Jupiter Perpetuals Liquidity Provider Token) 的成分與權重
# 我假設您圖片中的幣種為 JLP 的成分
JLP_COMPONENTS = {
    'SOL': 0.47,
    'ETH': 0.08,
    'WBTC': 0.13,
    'USDC': 0.32,
}

# 將成分幣對應到幣安的交易對 (使用 BTC 代表 WBTC)
COMPONENT_SYMBOLS_MAP = {
    'SOL': 'SOLUSDT',
    'ETH': 'ETHUSDT',
    'WBTC': 'BTCUSDT',
    'USDC': 'TUSDUSDT' # 使用 TUSD 作為 USDC 的替代品，因為幣安 USDCUSDT 數據可能不完整
}

# JLP 在 CoinMarketCap 上的資訊
JLP_CMC_SLUG = 'jupiter-perpetuals-liquidity-provider-token'

# --- API 設定 ---
if USE_SANDBOX:
    CMC_API_URL = 'https://sandbox-api.coinmarketcap.com/v2/cryptocurrency/quotes/historical'
else:
    CMC_API_URL = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/historical'

# --- 資料獲取功能 ---

def get_binance_historical_data(symbol, start_date_str, end_date_str):
    """從幣安獲取指定交易對的每日歷史價格"""
    print(f"正在從幣安獲取 {symbol} 的歷史資料...")
    start_ts = int(datetime.strptime(start_date_str, '%Y-%m-%d').timestamp() * 1000)
    end_ts = int(datetime.strptime(end_date_str, '%Y-%m-%d').timestamp() * 1000)

    params = {
        'symbol': symbol,
        'interval': '1d',
        'startTime': start_ts,
        'endTime': end_ts,
        'limit': 1000  # 單次請求最多1000筆
    }
    try:
        response = requests.get(BINANCE_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            print(f"警告：找不到 {symbol} 在指定區間的數據。")
            return pd.DataFrame(columns=['date', 'price'])

        df = pd.DataFrame(data, columns=[
            'open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time',
            'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
            'taker_buy_quote_asset_volume', 'ignore'
        ])
        df['date'] = pd.to_datetime(df['open_time'], unit='ms').dt.date
        df['price'] = pd.to_numeric(df['close'])
        return df[['date', 'price']]
    except requests.exceptions.RequestException as e:
        print(f"從幣安獲取 {symbol} 資料時出錯: {e}")
        return None

def get_cmc_historical_data(slug, start_date_str, end_date_str):
    """從 CoinMarketCap 獲取指定加密貨幣的每日歷史價格"""
    print(f"正在從 CoinMarketCap 獲取 {slug} 的歷史資料...")
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': CMC_API_KEY,
    }
    params = {
        'slug': slug,
        'time_start': start_date_str,
        'time_end': end_date_str,
        'interval': 'daily',
        'convert': 'USD'
    }
    try:
        response = requests.get(CMC_API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        quotes = data.get('data', {}).get('quotes', [])
        if not quotes:
            print(f"警告：找不到 {slug} 在指定區間的數據。")
            return pd.DataFrame(columns=['date', 'price'])
            
        price_list = []
        for q in quotes:
            timestamp = q['timestamp']
            price = q['quote']['USD']['close']
            price_list.append({'date': pd.to_datetime(timestamp).date(), 'price': price})
        
        return pd.DataFrame(price_list)
    except requests.exceptions.RequestException as e:
        print(f"從 CoinMarketCap 獲取 {slug} 資料時出錯: {e}")
        print(f"回應內容: {response.text}")
        return None

# --- 回測主程式 ---

def run_backtest():
    """執行整個回測流程"""
    print("--- 開始執行回測腳本 ---")
    
    # 1. 設定日期區間
    start_date = BACKTEST_START_DATE
    end_date = datetime.now().strftime('%Y-%m-%d')
    if datetime.strptime(start_date, '%Y-%m-%d') >= datetime.now():
        print("錯誤：開始日期在今天或未來，無法進行回測。")
        return

    print(f"回測區間: {start_date} 到 {end_date}")

    # 2. 獲取所有需要的歷史價格數據
    all_prices = {}
    
    # 獲取 JLP 價格
    jlp_prices = get_cmc_historical_data(JLP_CMC_SLUG, start_date, end_date)
    if jlp_prices is None or jlp_prices.empty:
        print("無法獲取 JLP 價格，終止回測。")
        return
    all_prices['JLP'] = jlp_prices.set_index('date')['price']

    # 獲取成分幣價格
    for component, symbol in COMPONENT_SYMBOLS_MAP.items():
        comp_prices = get_binance_historical_data(symbol, start_date, end_date)
        if comp_prices is None or comp_prices.empty:
            print(f"無法獲取 {component} ({symbol}) 價格，終止回測。")
            return
        all_prices[component] = comp_prices.set_index('date')['price']

    # 3. 合併與整理數據
    print("正在合併與對齊所有價格數據...")
    combined_df = pd.DataFrame(all_prices)
    combined_df.sort_index(inplace=True)
    
    # 使用前一天的數據填充週末或假日缺失的價格
    combined_df.ffill(inplace=True)
    combined_df.bfill(inplace=True) # 填充開頭可能缺失的數據

    if combined_df.empty:
        print("沒有足夠的數據來進行回測。")
        return

    print("數據準備完成，開始模擬交易...")
    
    # 4. 執行模擬
    first_day_prices = combined_df.iloc[0]
    
    # 計算初始倉位
    long_jlp_units = INITIAL_INVESTMENT / first_day_prices['JLP']
    short_component_units = {}
    for component, weight in JLP_COMPONENTS.items():
        value_to_short = INITIAL_INVESTMENT * weight
        price = first_day_prices[component]
        short_component_units[component] = value_to_short / price
        
    # 計算每日損益
    pnl_records = []
    for i in range(1, len(combined_df)):
        prev_prices = combined_df.iloc[i-1]
        curr_prices = combined_obj = combined_df.iloc[i]
        
        # 做多 JLP 的損益
        long_pnl = (curr_prices['JLP'] - prev_prices['JLP']) * long_jlp_units
        
        # 做空成分幣的損益
        short_pnl = 0
        for component, units in short_component_units.items():
            # (舊價格 - 新價格) * 數量
            short_pnl += (prev_prices[component] - curr_prices[component]) * units
            
        daily_pnl = long_pnl + short_pnl
        pnl_records.append({
            'date': combined_df.index[i],
            'daily_pnl': daily_pnl
        })
        
    # 5. 輸出結果
    if not pnl_records:
        print("無法計算損益，可能是因為數據天數不足。")
        return

    print("\n--- 回測結果 ---")
    results_df = pd.DataFrame(pnl_records).set_index('date')
    results_df['cumulative_pnl'] = results_df['daily_pnl'].cumsum()
    
    print("每日損益與累積損益:")
    print(results_df)

    total_pnl = results_df['cumulative_pnl'].iloc[-1]
    print(f"\n在回測期間 ({start_date} to {end_date})，總損益為: ${total_pnl:,.2f}")
    print("--- 回測結束 ---")


if __name__ == '__main__':
    run_backtest()

