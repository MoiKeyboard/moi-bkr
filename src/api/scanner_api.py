from fastapi import FastAPI, HTTPException
from src.analysis.market_scanner import MarketScanner
from typing import List
import uvicorn

app = FastAPI()
scanner = MarketScanner()


@app.get("/health")
async def health_check():
    return scanner.health_check()


@app.get("/trending")
async def get_trending():
    result = scanner.get_trending_stocks()
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.post("/scan")
async def trigger_scan():
    result = scanner.scan_and_analyze()
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


# @app.get("/watchlist")
# async def get_watchlist():
#     return scanner.get_watchlist_status()


# @app.post("/watchlist/add")
# async def add_to_watchlist(tickers: List[str]):
#     try:
#         scanner.add_tickers(tickers)
#         return {"status": "success", "message": f"Added {len(tickers)} tickers"}
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @app.post("/watchlist/remove")
# async def remove_from_watchlist(tickers: List[str]):
#     try:
#         scanner.remove_tickers(tickers)
#         return {"status": "success", "message": f"Removed {len(tickers)} tickers"}
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=str(e))
