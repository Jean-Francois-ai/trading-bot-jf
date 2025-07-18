import os
import logging
import ccxt
from dotenv import load_dotenv

# Configurer le logging
logging.basicConfig(
    filename='binance_client.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')

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

def submit_binance_order(symbol, alloc, position_type):
    """Soumet un ordre à Binance (non utilisé en test)."""
    try:
        binance = ccxt.binance({'apiKey': BINANCE_API_KEY, 'secret': BINANCE_API_SECRET})
        amount = alloc * 1000  # Exemple : 1000 EUR de capital
        side = 'buy' if position_type == 'buy' else 'sell'
        order = binance.create_market_order(symbol, side, amount)
        logger.info(f"Ordre soumis à Binance : {order}")
        return order
    except Exception as e:
        logger.error(f"Erreur soumission ordre Binance pour {symbol} : {str(e)}")
        return None
