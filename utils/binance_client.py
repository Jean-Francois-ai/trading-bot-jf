import os
import logging
from binance.client import Client
import ccxt.async_support as ccxt
from dotenv import load_dotenv

# Configurer le logging
logging.basicConfig(
    filename='binance_client.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

async def fetch_binance_prices(symbol):
    """Récupère les prix depuis Binance via CCXT."""
    try:
        binance = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'apiSecret': os.getenv('BINANCE_API_SECRET'),
            'enableRateLimit': True
        })
        ticker = await binance.fetch_ticker(symbol)
        await binance.close()
        prices = {
            'open': float(ticker['open']),
            'close': float(ticker['last'])
        }
        logger.info(f"Prix Binance pour {symbol} : {prices}")
        return prices
    except Exception as e:
        logger.error(f"Erreur récupération prix Binance pour {symbol} : {str(e)}")
        return None

async def submit_binance_order(symbol, alloc, position_type):
    """Passe un ordre sur Binance."""
    try:
        binance = Client(
            api_key=os.getenv('BINANCE_API_KEY'),
            api_secret=os.getenv('BINANCE_API_SECRET')
        )
        account = binance.get_account()
        btc_balance = next((float(b['free']) for b in account['balances'] if b['asset'] == 'BTC'), 0)
        if btc_balance < 0.015:
            logger.error(f"Balance insuffisante : {btc_balance} BTC disponible")
            return None
        quantity = (0.015 * alloc) / float(binance.get_symbol_info(symbol)['filters'][2]['minQty'])
        order = binance.create_market_order(symbol=symbol, side=position_type.upper(), quantity=quantity)
        logger.info(f"Ordre {position_type} passé pour {symbol} : {order}")
        return order
    except Exception as e:
        logger.error(f"Erreur passage ordre pour {symbol} : {str(e)}")
        return None
