import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from scipy.optimize import bisect
import logging
from .config import *

logger = logging.getLogger(__name__)

class StrategyEngine:
    def __init__(self):
        self.model = SVC(probability=True, kernel='rbf')
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def train_model(self, df_features, target_col='Target'):
        """
        Trains the SVM model on historical data.
        df_features: DataFrame containing X (features) and y (target).
        """
        # Create Target if not present (Direction: 1 if Close > Open next day?)
        # Strategy Definition: Buy if Next Day Return > 0
        if target_col not in df_features.columns:
            # Assuming 'close' exists
            returns = df_features['close'].pct_change().shift(-1)
            df_features[target_col] = np.where(returns > 0, 1, 0)
            df_features = df_features.dropna()
            
        X = df_features.drop(columns=[target_col, 'close', 'open', 'high', 'low', 'volume'], errors='ignore')
        y = df_features[target_col]
        
        # Scaling
        X_scaled = self.scaler.fit_transform(X)
        
        logger.info(f"Training SVM on {len(X)} samples...")
        self.model.fit(X_scaled, y)
        self.is_trained = True
        
    def predict_signal(self, current_features):
        """
        Predicts the probability of an Up move (Win Probability W).
        """
        if not self.is_trained:
            logger.error("Model not trained yet.")
            return 0.5
            
        # Reshape for single prediction
        features_scaled = self.scaler.transform(current_features.values.reshape(1, -1))
        # Probability of Class 1 (Up)
        prob_up = self.model.predict_proba(features_scaled)[0][1]
        return prob_up

class KellySolver:
    def __init__(self, alpha=ALPHA, beta=BETA):
        self.alpha = alpha
        self.beta = beta
        # Lambda (Risk Aversion) calculation derived from Drawdown Constraint
        # Formula: lambda = log(beta) / log(alpha)
        # Note: log is natural log by default in numpy, which is correct for ratios
        if np.log(self.alpha) == 0:
             self.lamb = 5 # Default safety
        else:
             self.lamb = np.log(self.beta) / np.log(self.alpha)
             
        logger.info(f"Kelly Solver Initialized. Risk Aversion Lambda: {self.lamb:.4f}")

    def _utility_derivative(self, b, W, R):
        """
        Derivative of the Power Utility function expectation set to 0.
        Equation: W * (1 + b*R)^(-lambda) * R - (1 - W) * (1 - b)^(-lambda) = 0?
        Wait, First Order Condition for Max E[ U(wealth) ]:
        Identify b that maximizes E[ (1+r)^(1-lambda) / (1-lambda) ].
        The FOC is: E[ (1+r)^(-lambda) * dr/db ] = 0
        Where r is return fraction. 
        If Win: r = b*R. If Loss: r = -b.
        Win Term: W * (1 + b*R)^(-lambda) * R
        Loss Term: (1 - W) * (1 - b)^(-lambda) * (-1)
        Equation: W * R * (1 + b*R)^(-lambda) - (1 - W) * (1 - b)^(-lambda) = 0
        """
        term_win = W * R * np.power(1 + b * R, -self.lamb)
        term_loss = (1 - W) * np.power(1 - b, -self.lamb)
        return term_win - term_loss

    def calculate_optimal_allocation(self, win_prob, avg_win_loss_ratio):
        """
        Calculates the optimal 'b' (fraction of capital) using Bisection.
        """
        W = win_prob
        R = avg_win_loss_ratio
        
        # 1. Check for Positive Expectancy
        # Kelly Condition: W * R - (1 - W) > 0  => W * (R + 1) > 1
        expected_edge = W * (R + 1) - 1
        if expected_edge <= 0:
            logger.info("Negative Expectancy. Allocation: 0%")
            return 0.0
            
        # 2. Solve for 'b' in range [0, 0.99] (Cannot bet 100% due to power utility singularity at b=1)
        try:
            # Check sign at boundaries
            # f(0) = W*R - (1-W) = Edge > 0 (Given above)
            # f(0.99) -> Large negative term dominated by (1-b)^-lamb
            # So root exists.
            
            # Using scipy bisect
            optimal_b = bisect(self._utility_derivative, 0, 0.99, args=(W, R))
            
            # 3. Apply Hard Cap
            final_b = min(optimal_b, MAX_POSITION_SIZE)
            
            return round(final_b, 4)
            
        except Exception as e:
            logger.error(f"Optimization failed: {e}. Defaulting to 0.")
            return 0.0

class SignalGenerator:
    def __init__(self, data_manager, strategy_engine, kelly_solver):
        self.dm = data_manager
        self.engine = strategy_engine
        self.kelly = kelly_solver
        
    def run_analysis(self):
        # 1. Get Data
        df = self.dm.get_combined_features()
        if df is None or len(df) < 300:
            logger.warning("Insufficient Data.")
            return None
            
        # 2. Train Model
        # Use simple Train/Test split for now (Training on past 1 year)
        train_df = df.iloc[:-1] # Use all except today/tomorrow
        current_features = df.drop(columns=['close', 'open', 'high', 'low', 'volume'], errors='ignore').iloc[-1]
        
        self.engine.train_model(train_df)
        
        # 3. Predict Direction (W)
        prob_up = self.engine.predict_signal(current_features)
        
        # 4. Estimate Win/Loss Ratio (R)
        # Simple estimation: AvgPctGain / AvgPctLoss of the underlying asset over last 60 days
        # In a real backtest, this should be the Strategy's R, but for now we proxy with Volatility/Trend R
        # Better: Use rolling returns of the asset
        recent_changes = df['close'].pct_change().tail(60)
        avg_gain = recent_changes[recent_changes > 0].mean()
        avg_loss = abs(recent_changes[recent_changes < 0].mean())
        if avg_loss == 0 or np.isnan(avg_loss):
            R = 1.0 # Fallback
        else:
            R = avg_gain / avg_loss
            
        # 5. Calculate Allocation (b)
        W = prob_up
        # For Put (Short), we use W_down = 1 - W
        
        signal = "HOLD"
        allocation = 0.0
        
        # Improved Strategy Filter: Price > 30MA?
        # Actually Improved Strategy says: Strategy Equity > MA.
        # Since we don't have strategy equity yet, we use Price > SMA(200) or similar regime filter as proxy
        # Or Price > SMA(30) as per text
        # sma_30 = df.ta.sma(length=30).iloc[-1]
        sma_30 = df['close'].rolling(window=30).mean().iloc[-1]
        close_price = df['close'].iloc[-1]
        
        trend_filter = close_price > sma_30
        
        if W > 0.55: # Conviction Threshold
            if trend_filter:
                allocation = self.kelly.calculate_optimal_allocation(W, R)
                signal = "BUY_CALL"
        elif W < 0.45:
            # Bearish
            # For Short, W_short = 1 - W
            W_short = 1.0 - W
            # Check Trend Filter (Price < SMA30 for shorts?)
            if close_price < sma_30:
                 allocation = self.kelly.calculate_optimal_allocation(W_short, R)
                 signal = "BUY_PUT"
                 
        return {
            "signal": signal,
            "allocation": allocation,
            "win_prob": W,
            "win_loss_ratio": R,
            "price": close_price
        }

if __name__ == "__main__":
    # Test stub
    pass
