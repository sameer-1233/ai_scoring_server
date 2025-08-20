🚀 AI Engineer Challenge – DeFi Wallet Scoring API
📌 Overview

This project implements an AI-powered scoring system for DeFi wallets based on their DEX (decentralized exchange) activity.

It is built with FastAPI, modularized into services, models, and utils, and structured to integrate with Kafka and MongoDB.
Since this was developed in Colab (mocked environment), Kafka & MongoDB are stubbed out, but the code is structured for real-world use.

🛠️ How to Run
🔹 Local (with uvicorn)
# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload


Then open:

http://localhost:8000/ → root info

http://localhost:8000/api/v1/health → health check

http://localhost:8000/api/v1/stats → service stats

http://localhost:8000/docs → Swagger API docs

🔹 Colab / Mock Mode

Since Kafka & MongoDB aren’t available in Colab, we added:

A mock Kafka service (kafka_service.py) that processes a given payload.

In Colab, tests are run directly with FastAPI’s TestClient.

Example:

from fastapi.testclient import TestClient
import app.main as main

client = TestClient(main.app)

payload = {
    "wallet_address": "0xABC123",
    "data": [
        {
            "protocolType": "dexes",
            "transactions": [
                {"action": "deposit", "timestamp": 1609459200,
                 "token0": {"amountUSD": 10000, "symbol": "USDC"}},
                {"action": "swap", "timestamp": 1609462800,
                 "tokenIn": {"amountUSD": 5000, "symbol": "USDC"},
                 "tokenOut": {"amountUSD": 5000, "symbol": "ETH"}}
            ]
        }
    ]
}

resp = client.post("/api/v1/score", json=payload)
print(resp.json())

📊 Example Inputs & Outputs
🔹 Input
{
  "wallet_address": "0xABC123",
  "data": [
    {
      "protocolType": "dexes",
      "transactions": [
        {
          "action": "deposit",
          "timestamp": 1609459200,
          "token0": {"amountUSD": 10000, "symbol": "USDC"}
        },
        {
          "action": "swap",
          "timestamp": 1609462800,
          "tokenIn": {"amountUSD": 5000, "symbol": "USDC"},
          "tokenOut": {"amountUSD": 5000, "symbol": "ETH"}
        }
      ]
    }
  ]
}

🔹 Output
{
  "wallet_address": "0xABC123",
  "zscore": "478.000000000000000000",
  "timestamp": 1755682702,
  "processing_time_ms": 14,
  "categories": [
    {
      "category": "dexes",
      "score": 478.0,
      "transaction_count": 2,
      "features": {
        "total_deposit_usd": 10000.0,
        "total_withdraw_usd": 0.0,
        "num_deposits": 1,
        "num_withdraws": 0,
        "withdraw_ratio": 0.0,
        "avg_hold_time_days": 644.46,
        "account_age_days": 0.01,
        "unique_pools": 1,
        "total_swap_volume": 5000.0,
        "num_swaps": 1,
        "unique_pools_swapped": 1,
        "avg_swap_size": 5000.0,
        "token_diversity_score": 25,
        "swap_frequency_score": 0.0,
        "user_tags": [
          "Medium LP",
          "Long-term Holder",
          "Casual Trader"
        ],
        "lp_score": 740.0,
        "swap_score": 85.0,
        "final_score": 478.0
      }
    }
  ]
}

🔧 What’s Mocked

Kafka → Replaced with run_kafka_loop() mock in Colab. In production, it would consume wallet events from Kafka.

MongoDB → Stubbed out with service functions (db.py). In production, would fetch token metadata & thresholds.

Config → Handled via Pydantic Settings; in Colab we use defaults/env vars.

Cloudflare Tunnel 

Install cloudflared:

wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb


Authenticate:

cloudflared tunnel login


Start tunnel:

cloudflared tunnel --url http://localhost:8000


Get a public .trycloudflare.com URL.

✅ Endpoints
Method	Endpoint	Description
GET	/	Service info
GET	/api/v1/health	Health check
GET	/api/v1/stats	Stats (processed, uptime, errors)
POST	/api/v1/score	Score a wallet’s transactions
📌 Deliverables

Modular code under app/models, app/services, app/utils.

FastAPI server (app/main.py).

Mock Kafka/Mongo integration for Colab.


Full working API with example scoring output.
