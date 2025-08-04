# Jupiter Arbitrage Bot

本專案是一個自動化的套利與再平衡機器人，整合 Gate.io 期貨、Jupiter (Solana) 以及 Telegram 通知，實現多資產自動監控與交易。

## 主要功能
- 從 Gate.io 取得 BTC、ETH、SOL 期貨價格與持倉資訊
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

1. 安裝依賴：

```bash
pip install -r requirements.txt
```

2. 設定環境變數與 config.json：
- 請將 `.env` 內的 API 金鑰、Telegram Token 等資訊填寫完整
- `config.json` 需包含 Gate.io host、MetaMask 地址、目標權重等

3. 執行主程式：

```bash
python main.py
```

## 主要參數說明

- `.env`：
    - `GATE_APIKEY`、`GATE_SECRET`：Gate.io API 金鑰
    - `TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`：Telegram Bot 設定
- `config.json`：
    - `metamask_address`：MetaMask 地址
    - `gate_host_live`、`gate_host_testnet`：Gate.io API Host
    - `target_weights`：各資產目標權重

## 主要函式說明

- `setup_gate_client()`：初始化 Gate.io API 客戶端
- `fetch_today_gate_price(symbol, api_instance)`：取得指定合約最新價格
- `fetch_jlp_price()`：取得 JLP 代幣價格
- `fetch_metamask_balance()`：查詢 MetaMask 餘額
- `fetch_gate_positions_size(api_instance)`：查詢 Gate.io 期貨持倉
- `place_order(contract, size, api_instance)`：下單 Gate.io 期貨
- `setup_telegram_bot()`：初始化 Telegram Bot
- `send_telegram_message(bot_token, chat_id, message)`：發送 Telegram 訊息

## 注意事項
- 請勿將 `.env`、`config.json`、`test.py` 等敏感或測試檔案上傳至公開倉庫
- 本專案僅供學術與技術交流，非任何投資建議

## 聯絡方式
Jack Huang | yanboh99@gmail.com
