from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

try:
    from backend.eg import TSLADashboard
except ModuleNotFoundError:
    from eg import TSLADashboard


ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
load_dotenv(ROOT / ".env")
PERIODS = {"1D", "1W", "1M", "3M", "1Y", "3Y", "ALL"}


class Question(BaseModel):
    question: str
    period: str = "ALL"


class SymbolRequest(BaseModel):
    symbol: str


def _parse_levels(value: Any) -> list[float]:
    if isinstance(value, list):
        return [float(item) for item in value]
    if pd.isna(value) or value == "":
        return []
    try:
        parsed = ast.literal_eval(str(value))
        if isinstance(parsed, list):
            return [float(item) for item in parsed]
    except (ValueError, SyntaxError, TypeError):
        return []
    return []


def _normalise_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Adapt accepted CSV spellings to the schema used by TSLADashboard."""
    aliases = {
        "timestamp": "Date",
        "date": "Date",
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    }
    frame = frame.rename(columns={column: aliases.get(column.lower(), column) for column in frame.columns})
    required = {"Date", "Open", "High", "Low", "Close", "Volume"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

    frame["Date"] = pd.to_datetime(frame["Date"])
    for column in ("Open", "High", "Low", "Close", "Volume"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=list(required)).sort_values("Date").reset_index(drop=True)
    direction = frame["direction"] if "direction" in frame else pd.Series("N", index=frame.index)
    support = frame["Support"] if "Support" in frame else pd.Series([[]] * len(frame), index=frame.index)
    resistance = frame["Resistance"] if "Resistance" in frame else pd.Series([[]] * len(frame), index=frame.index)
    frame["direction"] = direction.fillna("N").astype(str).str.upper()
    frame["Support"] = support.apply(_parse_levels)
    frame["Resistance"] = resistance.apply(_parse_levels)
    return frame


def _row_payload(row: pd.Series) -> dict[str, Any]:
    return {
        "time": row["Date"].strftime("%Y-%m-%d"),
        "open": float(row["Open"]),
        "high": float(row["High"]),
        "low": float(row["Low"]),
        "close": float(row["Close"]),
        "volume": float(row["Volume"]),
        "direction": str(row["direction"]),
        "support": row["Support"],
        "resistance": row["Resistance"],
    }


def _summary_payload(dashboard: TSLADashboard, period: str) -> dict[str, Any]:
    summary = dashboard.get_data_summary(period)
    filtered = dashboard.filter_data_by_period(period)
    if filtered is None or filtered.empty:
        return {}
    summary["neutral_days"] = int((~filtered["direction"].isin(["LONG", "SHORT"])).sum())
    return {key: (float(value) if hasattr(value, "item") else value) for key, value in summary.items()}


def _load_dashboard() -> TSLADashboard:
    dashboard = TSLADashboard()
    dashboard.data = None
    dashboard.symbol = None
    return dashboard


app = FastAPI(title="Stock Analysis API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

dashboard = _load_dashboard()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "symbol": dashboard.symbol or ""}


@app.get("/api/auth/config")
def auth_config() -> dict[str, str]:
    return {
        "url": os.getenv("SUPABASE_URL", ""),
        "anon_key": os.getenv("SUPABASE_ANON_KEY", ""),
    }


@app.get("/api/data")
def data(period: str = "ALL") -> dict[str, Any]:
    period = period.upper()
    if period not in PERIODS:
        raise HTTPException(status_code=400, detail=f"Unsupported period. Choose one of: {', '.join(sorted(PERIODS))}")
    filtered = dashboard.filter_data_by_period(period) if dashboard.data is not None else None
    return {
        "symbol": dashboard.symbol or "",
        "period": period,
        "rows": [] if filtered is None else [_row_payload(row) for _, row in filtered.iterrows()],
    }


@app.get("/api/summary")
def summary(period: str = "ALL") -> dict[str, Any]:
    period = period.upper()
    if period not in PERIODS:
        raise HTTPException(status_code=400, detail="Unsupported period")
    return _summary_payload(dashboard, period)


@app.post("/api/data/alphavantage")
def load_alphavantage(request: SymbolRequest) -> dict[str, Any]:
    symbol = request.symbol.strip().upper()
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not symbol:
        raise HTTPException(status_code=400, detail="Enter a stock symbol")
    if not api_key:
        raise HTTPException(status_code=503, detail="ALPHAVANTAGE_API_KEY is not configured in .env")

    loaded = dashboard.load_data(symbol=symbol, api_key=api_key)
    if loaded is None or loaded.empty:
        reason = dashboard.last_data_error or "Alpha Vantage returned an empty dataset."
        raise HTTPException(status_code=502, detail=f"Could not load {symbol}: {reason}")

    dashboard.data = _normalise_data(loaded)
    dashboard.symbol = symbol
    return {"symbol": symbol, "rows": len(dashboard.data)}


@app.post("/api/data/upload")
async def upload_data(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")
    try:
        contents = await file.read()
        frame = _normalise_data(pd.read_csv(pd.io.common.BytesIO(contents)))
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    dashboard.data = frame
    dashboard.symbol = os.path.splitext(file.filename)[0].upper()
    return {"symbol": dashboard.symbol, "rows": len(frame)}


@app.post("/api/ask")
def ask(question: Question) -> dict[str, str]:
    if not question.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    period = question.period.upper()
    if period not in PERIODS:
        raise HTTPException(status_code=400, detail="Unsupported period")
    return {"answer": dashboard.query_data_with_ai(question.question.strip(), period)}


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
