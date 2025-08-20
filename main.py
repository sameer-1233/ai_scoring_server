import time
from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse

from .models.dex_model import process_wallet_complete, preprocess_dex_transactions
from .services.kafka_service import run_kafka_loop # Import kafka_service

app = FastAPI(title="AI Scoring Server", version="1.0.0")

START_TIME = time.time()
STATS = {"processed": 0, "success": 0, "failure": 0, "last_ms": 0.0}

@app.get("/")
def root() -> Dict[str, Any]:
    return {"service": "ai-scoring-server", "version": "1.0.0", "status": "ok"}

@app.get("/api/v1/health")
def health() -> Dict[str, Any]:
    uptime = time.time() - START_TIME
    return {"status": "healthy", "uptime_seconds": round(uptime, 2)}

@app.get("/api/v1/stats")
def stats() -> Dict[str, Any]:
    uptime = time.time() - START_TIME
    return {
        "processed": STATS["processed"],
        "success": STATS["success"],
        "failure": STATS["failure"],
        "last_ms": STATS["last_ms"],
        "uptime_seconds": round(uptime, 2),
    }

def _to_native(obj):
    """Recursively convert numpy/pandas types to native Python types for JSON safety."""
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_native(v) for v in obj]
    t = str(type(obj)).lower()
    if "numpy" in t:
        try: return obj.item()
        except Exception: return float(obj)
    if hasattr(obj, "to_dict") and "pandas" in t:
        return _to_native(obj.to_dict())
    return obj

@app.post("/api/v1/score")
def score_wallet(payload: Dict[str, Any] = Body(...)) -> JSONResponse:
    t0 = time.time()
    STATS["processed"] += 1
    try:
        final_score, features = process_wallet_complete(payload)
        # Model signals empty / invalid
        if isinstance(features, dict) and features.get("error"):
            STATS["failure"] += 1
            processing_time_ms = int((time.time() - t0) * 1000)
            STATS["last_ms"] = processing_time_ms
            failure_msg = {
                "wallet_address": payload.get("wallet_address", ""),
                "error": features["error"],
                "timestamp": int(datetime.now().timestamp()),
                "processing_time_ms": processing_time_ms,
                "categories": [{
                    "category": "dexes",
                    "error": features["error"],
                    "transaction_count": 0
                }]
            }
            return JSONResponse(content=failure_msg, status_code=200)

        df = preprocess_dex_transactions(payload)
        processing_time_ms = int((time.time() - t0) * 1000)
        STATS["last_ms"] = processing_time_ms
        STATS["success"] += 1

        success_msg = {
            "wallet_address": payload.get("wallet_address", ""),
            "zscore": f"{final_score:.18f}",
            "timestamp": int(datetime.now().timestamp()),
            "processing_time_ms": processing_time_ms,
            "categories": [{
                "category": "dexes",
                "score": final_score,
                "transaction_count": int(len(df)),
                "features": {k: v for k, v in features.items() if k not in ["score_breakdown", "user_tags"]}
            }]
        }
        return JSONResponse(content=_to_native(success_msg), status_code=200)

    except Exception as e:
        STATS["failure"] += 1
        processing_time_ms = int((time.time() - t0) * 1000)
        STATS["last_ms"] = processing_time_ms
        failure_msg = {
            "wallet_address": payload.get("wallet_address", ""),
            "error": f"Unhandled error: {e}",
            "timestamp": int(datetime.now().timestamp()),
            "processing_time_ms": processing_time_ms,
            "categories": [{
                "category": "dexes",
                "error": "Unhandled error",
                "transaction_count": 0
            }]
        }
        return JSONResponse(content=failure_msg, status_code=500)