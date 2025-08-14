# Jupiter Arbitrage Bot

本專案是一個自動化的套利與再平衡機器人，整合 OKX 永續合約、Jupiter (Solana) 以及 Telegram 通知，實現多資產自動監控與交易。

## 主要功能
- 從 OKX 取得 BTC、ETH、SOL 期貨價格與持倉資訊
- 從 Jupiter API 取得 JLP 代幣價格與 MetaMask 餘額
- 根據自訂權重自動計算再平衡需求，並自動下單
- 交易完成後自動發送 Telegram 通知

## 專案結構

```
config.json         # 配置檔，包含 API host、目標權重、地址等
main.py             # 主程式，負責資產再平衡邏輯
utils.py            # 工具函式，API 請求、下單、餘額查詢等
readme.md           # 本說明文件
```

## 快速開始


1. 環境建立：
    - 建立虛擬環境 (可選)
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # 在 Windows 上請用 venv\Scripts\activate
    ```
    - 安裝必要套件
    ```bash
    pip install -r requirements.txt
    ```

2. 設定環境變數與 config.json：
- 請在專案根目錄建立 `.env` 與 `config.json`
- 將 `.env` 內的資訊填寫完整
- 將 `config.json` 內的資訊填寫完整

3. 執行主程式：

```bash
python3 main.py
```

## 主要參數說明

- `.env`：
    - `GATE_APIKEY`、`GATE_SECRET`：Gate.io API 金鑰
    - `TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`：Telegram Bot 設定
    -   ``` env
        GATE_APIKEY="YOUR_GATE_APIKEY"
        GATE_SECRET="YOUR_GATE_SECRET_KEY"
        OKX_APIKEY="YOUR_OKX_APIKEY"
        OKX_SECRET="YOUR_OKX_SECRET_KEY"
        OKX_PASSPHRASE="YOUR_OKX_PASSPHRASE"
        TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
        TELEGRAM_CHAT_ID="YOUR_TELEGRAM_CHAT_ID"
        ```

- `config.json`：
    - `metamask_address`：MetaMask 地址
    - `gate_host_live`、`gate_host_testnet`：Gate.io API Host
    - `target_weights`：各資產目標權重
    -   ``` json
        {
        "metamask_address": "YOUR_META_MASK_ADDRESS(SOLANA)",           // (MANDATORY)
        "gate_host_testnet": "https://api-testnet.gateapi.io/api/v4",   // (OPTIONAL)
        "gate_host_live": "https://api.gateio.ws/api/v4",               // (OPTIONAL)
        "okx_flag": "0",                                                // 0 for live trading, 1 for demo trading (MANDATORY)
        "target_weights": { 
            "JLP": 1, 
            "BTC": 0.13,
            "ETH": 0.08,
            "SOL": 0.47
            }
        }                                                               // (MANDATORY)
        ```

## 主要函式說明

- `setup_okx_client()`：初始化 OKX 客戶端
- `fetch_today_okx_price(symbol, marketDataAPI)`：取得指定合約最新價格
- `fetch_jlp_price()`：取得 JLP 代幣價格
- `fetch_metamask_balance()`：查詢 MetaMask 餘額
- `fetch_okx_positions_size(accountAPI)`：查詢 OKX 合約持倉
- `place_order(contract, size, tradAPI)`：下單 OKX 期貨，size 皆為最低下單數量
- `setup_telegram_bot()`：初始化 Telegram Bot
- `send_telegram_message(bot_token, chat_id, message)`：發送 Telegram 訊息
- `margin_call_check`：檢查做空倉位保證金餘額

## 注意事項
- 請勿將 `.env`、`config.json` 等敏感資訊上傳至公開倉庫
- 本專案僅供學術與技術交流，非任何投資建議

## 聯絡方式
Jack Huang | yanboh99@gmail.com
