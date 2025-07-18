import os
import logging
import alpaca_trade_api as tradeapi
import oandapyV20
import oandapyV20.endpoints.pricing as pricing
import krakenex
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta

# Configurer le logging
logging.basicConfig(
    filename='data_fetch.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Charger les variables d’environnement
load_dotenv()

# Configurer les APIs
try:
    alpaca_api = tradeapi.REST(
        key_id=os.getenv('ALPACA_API_KEY'),
        secret_key=os.getenv('ALPACA_SECRET_KEY'),
        base_url=os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),
        api_version='v2'
    )
    logger.info("Connexion à l’API Alpaca réussie.")
except Exception as e:
    logger.error(f"Erreur connexion Alpaca : {str(e)}")
    alpaca_api = None

try:
    oanda_client = oandapyV20.API(
        access_token=os.getenv('OANDA_API_KEY'),
        environment='practice'
    )
    logger.info("Connexion à l’API Oanda réussie.")
except Exception as e:
    logger.error(f"Erreur connexion Oanda : {str(e)}")
    oanda_client = None

try:
    kraken_api = krakenex.API(key=os.getenv('KRAKEN_API_KEY'), secret=os.getenv('KRAKEN_SECRET_KEY'))
    logger.info("Connexion à l’API Kraken réussie.")
except Exception as e:
    logger.error(f"Erreur connexion Kraken : {str(e)}")
    kraken_api = None

def fetch_yahoo_returns(symbol):
    """Récupère les rendements quotidiens via Alpaca, Oanda, ou Kraken."""
    # Mappage des symboles
    symbol_mapping = {
        'XETHZEUR': 'XETHZEUR',  # Kraken
        'USDCUSD': 'USDCUSD',     # Kraken
        'EURUSD': 'EUR_USD',      # Oanda
        'GBPUSD': 'GBP_USD',      # Oanda
        'USDJPY': 'USD_JPY',      # Oanda
        'XAUUSD': 'XAU_USD',      # Oanda
        'UKOIL': 'WTICO_USD',    # Oanda
        'NGAS': 'NATGAS_USD'      # Oanda
    }
    mapped_symbol = symbol_mapping.get(symbol, symbol)

    # Alpaca pour indices/ETF
    if symbol in ['SPY', 'QQQ', 'IWM', 'AAPL', 'VXX']:
        try:
            end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
            bars = alpaca_api.get_bars(symbol, '1D', start=start_date, end=end_date).df
            logger.info(f"Données Alpaca pour {symbol} : {bars}")
            if not bars.empty and len(bars['close']) >= 2:
                returns = bars['close'].pct_change().dropna().values
                logger.info(f"Rendements Alpaca pour {symbol} : {returns}")
                return returns
            else:
                logger.warning(f"Données insuffisantes Alpaca pour {symbol} : {len(bars['close'])} jour(s)")
                return [0]
        except Exception as e:
            logger.error(f"Erreur Alpaca pour {symbol} : {str(e)}")
            return [0]

    # Oanda pour forex/commodities
    elif mapped_symbol in ['EUR_USD', 'GBP_USD', 'USD_JPY', 'XAU_USD', 'WTICO_USD', 'NATGAS_USD']:
        try:
            params = {'instruments': mapped_symbol}
            r = pricing.PricingInfo(accountID=os.getenv('OANDA_ACCOUNT_ID'), params=params)
            oanda_client.request(r)
            price = r.response['prices'][0]
            close = float(price['closeoutAsk'])
            open_price = float(price['bids'][0]['price'])
            returns = [(close - open_price) / open_price] if open_price != 0 else [0]
            logger.info(f"Prix Oanda pour {symbol} : close={close}, open={open_price}, rendement={returns}")
            return returns
        except Exception as e:
            logger.error(f"Erreur Oanda pour {symbol} : {str(e)}")
            return [0]

    # Kraken pour cryptos
    elif mapped_symbol in ['XETHZEUR', 'USDCUSD']:
        try:
            ticker = kraken_api.query_public('Ticker', {'pair': mapped_symbol})['result'][mapped_symbol]
            close = float(ticker['c'][0])
            open_price = float(ticker['o'])
            returns = [(close - open_price) / open_price] if open_price != 0 else [0]
            logger.info(f"Prix Kraken pour {symbol} : close={close}, open={open_price}, rendement={returns}")
            return returns
        except Exception as e:
            logger.error(f"Erreur Kraken pour {symbol} : {str(e)}")
            return [0]

    # Valeur par défaut
    logger.warning(f"Symbole {symbol} non pris en charge")
    return [0]

def fetch_option_chain(symbol):
    return {"calls": [], "puts": []}

def fetch_alpha_vantage_intraday(symbol):
    return []

def fetch_alpha_vantage_earnings(symbol):
    return []
