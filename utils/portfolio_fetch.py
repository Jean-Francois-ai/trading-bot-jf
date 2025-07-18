import os
import logging
import alpaca_trade_api as tradeapi
import oandapyV20
import oandapyV20.endpoints.accounts as accounts
import krakenex
from dotenv import load_dotenv

# Configurer le logging
logging.basicConfig(
    filename='portfolio_fetch.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

def fetch_portfolio():
    """Récupère le portefeuille depuis Alpaca, Oanda, et Kraken."""
    portfolio = {}
    
    # Alpaca
    try:
        alpaca_api = tradeapi.REST(
            key_id=os.getenv('ALPACA_API_KEY'),
            secret_key=os.getenv('ALPACA_SECRET_KEY'),
            base_url=os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),
            api_version='v2'
        )
        account = alpaca_api.get_account()
        portfolio['alpaca'] = {
            'balance': float(account.cash),
            'portfolio_value': float(account.portfolio_value)
        }
        logger.info(f"Portefeuille Alpaca : {portfolio['alpaca']}")
    except Exception as e:
        logger.error(f"Erreur Alpaca : {str(e)}")
        portfolio['alpaca'] = {'balance': 0, 'portfolio_value': 0}

    # Oanda
    try:
        oanda_client = oandapyV20.API(
            access_token=os.getenv('OANDA_API_KEY'),
            environment='practice'
        )
        r = accounts.AccountDetails(accountID=os.getenv('OANDA_ACCOUNT_ID'))
        oanda_client.request(r)
        account = r.response['account']
        portfolio['oanda'] = {
            'balance': float(account['balance']),
            'nav': float(account['NAV'])
        }
        logger.info(f"Portefeuille Oanda : {portfolio['oanda']}")
    except Exception as e:
        logger.error(f"Erreur Oanda : {str(e)}")
        portfolio['oanda'] = {'balance': 0, 'nav': 0}

    # Kraken
    try:
        kraken_api = krakenex.API(key=os.getenv('KRAKEN_API_KEY'), secret=os.getenv('KRAKEN_SECRET_KEY'))
        balance = kraken_api.query_private('Balance')['result']
        portfolio['kraken'] = {
            'balance': sum(float(v) for v in balance.values()) if balance else 0
        }
        logger.info(f"Portefeuille Kraken : {portfolio['kraken']}")
    except Exception as e:
        logger.error(f"Erreur Kraken : {str(e)}")
        portfolio['kraken'] = {'balance': 0}

    return portfolio
