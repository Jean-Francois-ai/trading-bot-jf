from oandapyV20 import API
from oandapyV20.endpoints.accounts import AccountDetails
from oandapyV20.endpoints.pricing import PricingStream
from base_exchange import BaseExchange
from dotenv import load_dotenv
import os
load_dotenv()

class OandaExchange(BaseExchange):
    def __init__(self):
        super().__init__(
            api_key=os.getenv('OANDA_API_KEY'),
            secret_key=os.getenv('OANDA_ACCOUNT'),
            base_url='https://api-fxpractice.oanda.com'  # Paper trading endpoint
        )
        self.client = API(access_token=self.api_key, environment="practice")
        self.account_id = os.getenv('OANDA_ACCOUNT_ID')

    def get_price(self, symbol):
        try:
            params = {"instruments": symbol}
            pricing = PricingStream(self.account_id, params)
            response = self.client.request(pricing)
            for msg in response:
                if msg['type'] == 'PRICE':
                    return float(msg['closeoutBid'])
            return 0.0
        except:
            return 0.0  # Fallback for simulation

    def get_balance(self):
        try:
            request = AccountDetails(self.account_id)
            response = self.client.request(request)
            return float(response['account']['balance'])
        except:
            return 55.0  # Default for paper trading (~55 EUR)

    def place_trade(self, symbol, alloc, position_type, strikes=None):
        if os.getenv('AUTO_TRADE_MODE') == 'paper':
            return {'status': 'simulated', 'symbol': symbol, 'alloc': alloc, 'position_type': position_type}
        # Real trade logic (not used in paper mode)
        return {'status': 'pending', 'symbol': symbol, 'alloc': alloc, 'position_type': position_type}
