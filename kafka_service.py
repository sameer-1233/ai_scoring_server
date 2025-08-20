
from confluent_kafka import Consumer, Producer
import json, time
from app.models.dex_model import process_wallet_complete, preprocess_dex_transactions
from app.config import settings

def run_kafka_loop(stats=None):
    consumer = Consumer({
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "group.id": settings.kafka_consumer_group,
        "auto.offset.reset": "earliest",
    })
    producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})
    consumer.subscribe([settings.kafka_input_topic])

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print("Consumer error:", msg.error())
                if stats: stats["errors"] += 1
                continue

            payload = json.loads(msg.value())
            start = time.time()

            try:
                final_score, features = process_wallet_complete(payload)
                elapsed = int((time.time() - start) * 1000)

                if isinstance(features, dict) and features.get("error"):
                    out = {
                        "wallet_address": payload.get("wallet_address",""),
                        "error": features["error"],
                        "timestamp": int(time.time()),
                        "processing_time_ms": elapsed,
                        "categories": [{"category":"dexes","error":features["error"],"transaction_count":0}]
                    }
                    producer.produce(settings.kafka_failure_topic, json.dumps(out).encode())
                    if stats: stats["errors"] += 1
                else:
                    df = preprocess_dex_transactions(payload)
                    out = {
                        "wallet_address": payload.get("wallet_address",""),
                        "zscore": f"{final_score:.18f}",
                        "timestamp": int(time.time()),
                        "processing_time_ms": elapsed,
                        "categories": [{
                            "category":"dexes",
                            "score": final_score,
                            "transaction_count": int(len(df)),
                            "features": features
                        }]
                    }
                    producer.produce(settings.kafka_success_topic, json.dumps(out).encode())
                    if stats: stats["processed"] += 1
                producer.poll(0)

            except Exception as e:
                err = {
                    "wallet_address": payload.get("wallet_address",""),
                    "error": f"Unhandled error: {e}",
                    "timestamp": int(time.time()),
                    "processing_time_ms": 0,
                    "categories": [{"category":"dexes","error":"Unhandled error","transaction_count":0}]
                }
                producer.produce(settings.kafka_failure_topic, json.dumps(err).encode())
                producer.poll(0)
                if stats: stats["errors"] += 1
    finally:
        consumer.close()
