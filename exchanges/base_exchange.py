class BaseExchange:
    def __init__(self, api_key, secret_key, base_url):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url

    def get_price(self, symbol):
        raise NotImplementedError

    def get_balance(self):
        raise NotImplementedError

    def place_trade(self, symbol, alloc, position_type, strikes=None):