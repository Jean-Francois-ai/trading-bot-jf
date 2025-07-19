import os
import logging
from binance.client import Client
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
    """Récupère le portefeuille depuis Binance uniquement."""
    portfolio = {}
    
    # Binance
    try:
        binance_client = Client(
            api_key=os.getenv('BINANCE_API_KEY'),
            api_secret=os.getenv('BINANCE_API_SECRET')
        )
        account = binance_client.get_account()
        balances = account['balances']
        total_balance = sum(float(balance['free']) + float(balance['locked']) for balance in balances if float(balance['free']) > 0 or float(balance['locked']) > 0)
        portfolio['binance'] = {
            'balance': total_balance
        }
        logger.info(f"Portefeuille Binance : {portfolio['binance']}")
    except Exception as e:
        logger.error(f"Erreur Binance : {str(e)}")
        portfolio['binance'] = {'balance': 0}

    return portfolio
