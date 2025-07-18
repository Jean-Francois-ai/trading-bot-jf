from alpaca_trade_api.rest import REST
from base_exchange import BaseExchange
from dotenv import load_dotenv
import os
load_dotenv()

class AlpacaExchange(BaseExchange):
    def __init__(self):
        super().__init__(
            api_key=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            base_url='https://paper-api.alpaca.markets'  # Paper trading endpoint
        )
        self.client = REST(self.api_key, self.secret_key, self.base_url)

    def get_price(self, symbol):
        try:
            return float(self.client.get_latest_trade(symbol).price)
        except:
            return 0.0  # Fallback for simulation

    def get_balance(self):
        try:
            return float(self.client.get_account().cash)
        except:
            return 184.0  # Default for paper trading (~184 EUR)

    def place_trade(self, symbol, alloc, position_type, strikes=None):
        if os.getenv('AUTO_TRADE_MODE') == 'paper':
            return {'status': 'simulated', 'symbol': symbol, 'alloc': alloc, 'position_type': position_type, 'strikes': strikes}
        # Real trade logic (not used in paper mode)
        return {'status': 'pending', 'symbol': symbol, 'alloc': alloc, 'position_type': position_type}
