from krakenex import API
from base_exchange import BaseExchange
from dotenv import load_dotenv
import os
load_dotenv()

class KrakenExchange(BaseExchange):
    def __init__(self):
        super().__init__(
            api_key=os.getenv('KRAKEN_API_KEY'),
            secret_key=os.getenv('KRAKEN_SECRET_KEY'),
            base_url='https://futures.kraken.com'  # Paper trading endpoint
        )
        self.client = API(key=self.api_key, secret=self.secret_key)

    def get_price(self, symbol):
        try:
            response = self.client.query_public('Ticker', {'pair': symbol})
            return float(response['result'][symbol]['last'])
        except:
            return 0.0  # Fallback for simulation

    def get_balance(self):
        try:
            response = self.client.query_private('Balance')
            return float(response['result']['total'])
        except:
            return 500.0  # Default for paper trading (~500 EUR)

    def place_trade(self, symbol, alloc, position_type, strikes=None):
        if os.getenv('AUTO_TRADE_MODE') == 'paper':
            return {'status': 'simulated', 'symbol': symbol, 'alloc': alloc, 'position_type': position_type}
        # Real trade logic (not used in paper mode)
        return {'status': 'pending', 'symbol': symbol, 'alloc': alloc, 'position_type': position_type}
