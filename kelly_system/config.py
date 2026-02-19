import os
from dotenv import load_dotenv

# Load environment variables (Override to pick up fresh tokens)
load_dotenv(override=True)

# --- Authentication ---
API_KEY = os.getenv("KITE_API_KEY")
API_SECRET = os.getenv("KITE_API_SECRET")
ACCESS_TOKEN = os.getenv("KITE_ACCESS_TOKEN")

# --- Instrument Tokens ---
# NIFTY 50 (NSE Index) - ID: 256265
# GIFT NIFTY (NSEIX Futures) - ID: 291849
NIFTY_50_TOKEN = 256265
GIFT_NIFTY_TOKEN = 291849 # NSEIX:GIFT NIFTY

# --- Global Tickers (Yahoo Finance) ---
GLOBAL_TICKERS = {
    "DJIA": "^DJI",         # Dow Jones Industrial Average
    "GOLD": "GC=F",         # Gold Futures
    "US10Y": "^TNX",        # CBOE Interest Rate 10 Year T Note
    "DOLLAR_IDX": "DX-Y.NYB" # US Dollar Index
}

# --- Risk Management (Kelly Criterion) ---
# Alpha: Disaster level (e.g., 0.8 means max 20% drawdown)
ALPHA = 0.8 
# Beta: Confidence level (e.g., 0.05 means 95% confidence)
BETA = 0.05
# Max Position Size (as fraction of capital, hard cap)
MAX_POSITION_SIZE = 0.20 
# Stop Loss (Fixed % per trade)
STOP_LOSS_PCT = 0.08

# --- Strategy Parameters ---
# "Improved Strategy": Trade only if Equity > MA(30)
EQUITY_MA_WINDOW = 30
# SVM Lookback
SVM_LOOKBACK_DAYS = 252 # 1 Trading Year
# Re-training Frequency
RETRAIN_DAYS = 1 # Retrain daily
