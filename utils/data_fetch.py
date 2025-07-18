import os
import logging
import oandapyV20
from oandapyV20.endpoints.pricing import PricingInfo
from dotenv import load_dotenv
import requests
import ccxt

# Configurer le logging
logging.basicConfig(
    filename='data_fetch.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
OANDA_API_KEY = os.getenv('OANDA_API_KEY')
OANDA_ACCOUNT_ID = os.getenv('OANDA_ACCOUNT_ID')
KRAKEN_API_KEY = os.getenv('KRAKEN_API_KEY')
KRAKEN_API_SECRET = os.getenv('KRAKEN_API_SECRET')
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

def fetch_oanda_prices(symbol):
    """Récupère les prix Oanda pour un symbole donné."""
    try:
        if not OANDA_API_KEY or not OANDA_ACCOUNT_ID:
            logger.error("OANDA_API_KEY ou OANDA_ACCOUNT_ID manquant dans .env")
            return [0]
        client = oandapyV20.API(access_token=OANDA_API_KEY, environment="practice")
        params = {"instruments": symbol}
        request = PricingInfo(accountID=OANDA_ACCOUNT_ID, params=params)
        response = client.request(request)
        prices = response['prices'][0]
        close = float(prices['closeoutBid'])
        open_price = float(prices['closeoutAsk'])
        logger.info(f"Prix Oanda pour {symbol} : close={close}, open={open_price}, rendement=[{(close - open_price) / open_price}]")
        return [(close - open_price) / open_price]
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur réseau récupération prix Oanda pour {symbol} : {str(e)}")
        return [0]
    except Exception as e:
        logger.error(f"Erreur récupération prix Oanda pour {symbol} : {str(e)}")
        return [0]

def fetch_kraken_prices(symbol):
    """Récupère les prix Kraken pour un symbole donné."""
    try:
        if not KRAKEN_API_KEY or not KRAKEN_API_SECRET:
            logger.error("KRAKEN_API_KEY ou KRAKEN_API_SECRET manquant dans .env")
            return [0]
        kraken = ccxt.kraken({'apiKey': KRAKEN_API_KEY, 'secret': KRAKEN_API_SECRET})
        ticker = kraken.fetch_ticker(symbol)
        close = ticker['close']
        open_price = ticker['open'] if 'open' in ticker else close
        logger.info(f"Prix Kraken pour {symbol} : close={close}, open={open_price}, rendement=[{(close - open_price) / open_price}]")
        return [(close - open_price) / open_price]
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur réseau récupération prix Kraken pour {symbol} : {str(e)}")
        return [0]
    except Exception as e:
        logger.error(f"Erreur récupération prix Kraken pour {symbol} : {str(e)}")
        return [0]

def fetch_binance_prices(symbol):
    """Récupère les prix Binance pour un symbole donné."""
    try:
        if not BINANCE_API_KEY or not BINANCE_API_SECRET:
            logger.error("BINANCE_API_KEY ou BINANCE_API_SECRET manquant dans .env")
            return [0]
        binance = ccxt.binance({'apiKey': BINANCE_API_KEY, 'secret': BINANCE_API_SECRET})
        ticker = binance.fetch_ticker(symbol)
        close = ticker['close']
        open_price = ticker['open'] if 'open' in ticker else close
        logger.info(f"Prix Binance pour {symbol} : close={close}, open={open_price}, rendement=[{(close - open_price) / open_price}]")
        return [(close - open_price) / open_price]
    except Exception as e:
        logger.error(f"Erreur récupération prix Binance pour {symbol} : {str(e)}")
        return [0]
