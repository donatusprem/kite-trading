import pandas as pd
# import pandas_ta as ta # Removed, using 'ta' library inside method
# import pandas_ta as ta
import yfinance as yf
from kiteconnect import KiteConnect
import datetime
import logging
import time
from .config import *

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketDataManager:
    def __init__(self, api_key=API_KEY, access_token=ACCESS_TOKEN):
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        
    def fetch_nifty_data(self, days=365, interval='day'):
        """Fetches Nifty 50 OHLC data from yfinance (Free Tier Support)."""
        # Kite 'history' API is paid. Using yfinance as fallback.
        ticker = "^NSEI" 
        start_date = (datetime.datetime.now() - datetime.timedelta(days=days + 20)).strftime('%Y-%m-%d')
        
        logger.info(f"Fetching Nifty 50 data ({ticker}) via yfinance...")
        try:
            df = yf.download(ticker, start=start_date, progress=False)
            if df.empty:
                logger.warning("No Nifty data returned from yfinance.")
                return pd.DataFrame()
            
            # Standardize Columns
            if isinstance(df.columns, pd.MultiIndex):
                # Flatten
                df.columns = [c[0].lower() for c in df.columns]
                # yf returns 'adj close', 'close', etc.
                if 'adj close' in df.columns:
                    df['close'] = df['adj close']
            else:
                df.columns = [c.lower() for c in df.columns]

            # Ensure 'close', 'open', 'high', 'low', 'volume' exist
            required = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required):
                logger.error(f"Missing columns in yfinance data: {df.columns}")
                return pd.DataFrame()
                
            df['date'] = df.index.date
            # df.set_index('date', inplace=True) # yfinance index is already datetime
            return df[required]

        except Exception as e:
            logger.error(f"Error fetching Nifty data from yfinance: {e}")
            return pd.DataFrame()

    def fetch_gift_nifty_data(self, days=365, interval='day'):
        """Fetches GIFT Nifty data from Kite (NSEIX)."""
        to_date = datetime.datetime.now().date()
        from_date = to_date - datetime.timedelta(days=days)
        
        logger.info(f"Fetching GIFT Nifty data...")
        try:
            records = self.kite.historical_data(
                instrument_token=GIFT_NIFTY_TOKEN,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            df = pd.DataFrame(records)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date']).dt.date
                df.set_index('date', inplace=True)
                df.rename(columns={'close': 'GIFT_NIFTY'}, inplace=True)
                return df[['GIFT_NIFTY']]
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching GIFT Nifty: {e}")
            return pd.DataFrame()

    def fetch_global_indices(self, start_date=None):
        """Fetches Global Indicators (DJIA, Gold, US10Y) via yfinance."""
        if not start_date:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=400)).strftime('%Y-%m-%d')
            
        logger.info("Fetching Global Indicators from yfinance...")
        data_frames = []
        for name, ticker in GLOBAL_TICKERS.items():
            try:
                df = yf.download(ticker, start=start_date, progress=False)
                if not df.empty:
                    # Handle MultiIndex if present
                    if isinstance(df.columns, pd.MultiIndex):
                         df = df['Close'] # Just take Close
                    else:
                         df = df[['Close']]
                         
                    df.columns = [name]
                    df.index = df.index.date
                    data_frames.append(df)
            except Exception as e:
                logger.error(f"Error fetching {name} ({ticker}): {e}")
        
        if data_frames:
            combined = pd.concat(data_frames, axis=1)
            return combined
        return pd.DataFrame()

    def get_nifty_atm_option(self, spot_price, transaction_type, expiry_offset=0):
        """
        Finds the ATM Option Symbol.
        transaction_type: 'CE' or 'PE'
        expiry_offset: 0 for current week, 1 for next week
        """
        # 1. Round Spot to nearest 50
        strike_price = round(spot_price / 50) * 50
        
        # 2. Get All NFO Instruments (Cached ideally, but fetching for robustness)
        # Note: This is a heavy call (~10MB). In production, fetch once at startup.
        try:
            logger.info("Fetching NFO Instruments...")
            instruments = self.kite.instruments("NFO")
            df_ins = pd.DataFrame(instruments)
            
            # Filter for NIFTY
            df_nifty = df_ins[df_ins['name'] == 'NIFTY']
            
            # Filter by Strike and Type
            df_strike = df_nifty[
                (df_nifty['strike'] == strike_price) & 
                (df_nifty['instrument_type'] == transaction_type)
            ]
            
            # Sort by Expiry
            df_strike['expiry'] = pd.to_datetime(df_strike['expiry'])
            df_strike.sort_values('expiry', inplace=True)
            
            # Select Expiry (Current vs Next)
            # Filter out expired contracts
            today = datetime.datetime.now()
            df_valid = df_strike[df_strike['expiry'] >= today]
            
            if len(df_valid) > expiry_offset:
                selected_ins = df_valid.iloc[expiry_offset]
                return {
                    "tradingsymbol": selected_ins['tradingsymbol'],
                    "instrument_token": selected_ins['instrument_token'],
                    "lot_size": selected_ins['lot_size'],
                    "expiry": selected_ins['expiry']
                }
            else:
                logger.warning("No valid option found.")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching option symbol: {e}")
            return None

    def get_combined_features(self):
        """
        Aggregates Nifty, GIFT Nifty, Global Data, and Technical Indicators.
        Returns a DataFrame ready for SVM training.
        """
        # 1. Fetch Core Data (Increase history to 1000 days to account for 200SMA + 252 Training)
        nifty = self.fetch_nifty_data(days=1000)
        gift = self.fetch_gift_nifty_data(days=1000)
        globals_df = self.fetch_global_indices(start_date=(datetime.datetime.now() - datetime.timedelta(days=1000)).strftime('%Y-%m-%d'))
        
        if nifty.empty:
            logger.error("Critical: Nifty Data Missing.")
            return None

        # 2. Merge Data (Left Join on Nifty Dates)
        df = nifty.join(gift, how='left')
        df = df.join(globals_df, how='left')
        
        # 3. Forward Fill Global/GIFT Data (to handle trading holiday diffs)
        df.ffill(inplace=True)
        
        # 4. Feature Engineering (using 'ta' library)
        logger.info("Generating Technical Indicators (ta library)...")
        try:
            import ta
            
            # Momentum
            df['rsi'] = ta.momentum.rsi(df['close'], window=14)
            df['cci'] = ta.trend.cci(df['high'], df['low'], df['close'], window=20)
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
            
            # Volatility
            bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['close']
            
            df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
            
            # Trend
            df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
            df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
            df['sma_200'] = ta.trend.sma_indicator(df['close'], window=200)
            df['adx'] = ta.trend.adx(df['high'], df['low'], df['close'], window=14)

        except ImportError:
            logger.error("Library 'ta' not found. Please install: pip install ta")
            return None
        except Exception as e:
            logger.error(f"Error computing indicators: {e}")
            return None

        # 5. Clean NaN (Drop initial rows required for indicators)
        df.dropna(inplace=True)
        
        logger.info(f"Feature Engineering Complete. Shape: {df.shape}")
        return df

    def fetch_portfolio(self):
        """Fetches Holdings and Positions from Kite."""
        try:
            holdings = self.kite.holdings()
            positions = self.kite.positions()
            return {
                "holdings": holdings,
                "positions": positions,
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error fetching portfolio: {e}")
            return {"holdings": [], "positions": {}, "error": str(e)}

if __name__ == "__main__":
    # Test Run
    dm = MarketDataManager()
    df = dm.get_combined_features()
    if df is not None:
        print(df.tail())
        print("Columns:", df.columns.tolist())
