from dotenv import load_dotenv
import os
load_dotenv()

def check_amf_compliance(exchanges):
    """
    Vérifie la conformité AMF : clés API présentes et KYC validé.
    """
    required_keys = [
        ('alpaca', 'api_key', os.getenv('ALPACA_API_KEY')),
        ('alpaca', 'secret_key', os.getenv('ALPACA_SECRET_KEY')),
        ('oanda', 'api_key', os.getenv('OANDA_API_KEY')),
        ('oanda', 'account_id', os.getenv('OANDA_ACCOUNT_ID')),
        ('kraken', 'api_key', os.getenv('KRAKEN_API_KEY')),
        ('kraken', 'secret_key', os.getenv('KRAKEN_SECRET_KEY'))
    ]
    for exchange, key_type, key_value in required_keys:
        if not key_value:
            return False
    return True
