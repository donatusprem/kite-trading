import logging
import math
from .config import *

logger = logging.getLogger(__name__)

class OrderManager:
    def __init__(self, data_manager):
        self.dm = data_manager
        self.kite = data_manager.kite
        
    def calculate_suggestion(self, signal_dict):
        """
        Calculates the trade details (Symbol, Lots, Price) without executing.
        Returns: { 'symbol': 'NIFTY24000CE', 'lots': 10, 'qty': 500, 'price': 120.5, 'capital': 50000 }
        """
        signal_type = signal_dict.get('signal')
        allocation = signal_dict.get('allocation', 0.0)
        spot_price = signal_dict.get('price')
        
        if signal_type == "HOLD" or allocation <= 0:
            return None
            
        # 1. Determine Instrument Type
        txn_type = "CE" if "CALL" in signal_type else "PE"
        
        # 2. Get Option Symbol (ATM)
        try:
            option_data = self.dm.get_nifty_atm_option(spot_price, txn_type)
        except Exception:
            option_data = None
            
        if not option_data:
            return {"error": "Could not find Option Symbol"}
            
        symbol = option_data['tradingsymbol']
        lot_size = option_data['lot_size']
        
        # 3. Calculate Quantity based on Live Margin
        try:
            margins = self.kite.margins()
            available_cash = margins['equity']['net']
        except Exception:
            available_cash = 0 # Default to 0 if fails, user needs to know they have no dash
            # For Dry Run / Dashboard purpose, maybe show potential?
            # avail_cash = 100000 
            
        trade_capital = available_cash * allocation
        
        # Fetch Price
        ltp_data = self.kite.ltp(f"NFO:{symbol}")
        instrument_key = f"NFO:{symbol}"
        if instrument_key in ltp_data:
            option_price = ltp_data[instrument_key]['last_price']
        else:
            option_price = 0
            return {"error": "Could not fetch Option Price"}
            
        if option_price > 0:
            quantity_needed = int(trade_capital / option_price)
            num_lots = math.floor(quantity_needed / lot_size)
        else:
            num_lots = 0
            
        qty = num_lots * lot_size
        
        return {
            "symbol": symbol,
            "transaction_type": txn_type,
            "lots": num_lots,
            "quantity": qty,
            "price": option_price,
            "capital_required": qty * option_price,
            "available_cash": available_cash
        }

    def execute_strategy_signal(self, signal_dict):
        """
        Executes the trade based on the Signal Dictionary.
        """
        suggestion = self.calculate_suggestion(signal_dict)
        if not suggestion or "error" in suggestion:
            logger.error(f"Cannot execute: {suggestion}")
            return

        symbol = suggestion['symbol']
        quantity = suggestion['quantity']
        txn_type = suggestion['transaction_type']
        option_price = suggestion['price']
        
        if quantity <= 0:
             logger.warning("Calculated Quantity is 0. Insufficient Capital or Allocation.")
             return

        logger.info(f"Placing Order: {txn_type} {symbol} | Qty: {quantity}")
        
        # ... (Rest of execution logic similar to before, simplified)
        
        try:
            order_id = self.kite.place_order(
                tradingsymbol=symbol,
                exchange=self.kite.EXCHANGE_NFO,
                transaction_type=self.kite.TRANSACTION_TYPE_BUY,
                quantity=quantity,
                variety=self.kite.VARIETY_REGULAR,
                order_type=self.kite.ORDER_TYPE_MARKET,
                product=self.kite.PRODUCT_NRML,
                validity=self.kite.VALIDITY_DAY
            )
            logger.info(f"Entry Order Placed. ID: {order_id}")
            return order_id
        except Exception as e:
            logger.error(f"Order Placement Failed: {e}")
            return None
