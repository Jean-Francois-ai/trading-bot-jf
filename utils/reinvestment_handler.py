import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from utils.portfolio_fetch import fetch_portfolio

# Configurer le logging
logging.basicConfig(
    filename='reinvestment.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

def reinvest_gains(strategy_json):
    """Réinvestit les gains dans le portefeuille."""
    try:
        portfolio = fetch_portfolio()
        balance = 0
        for exchange, data in portfolio.items():
            if isinstance(data, dict) and 'balance' in data:
                balance += float(data['balance'])
            elif isinstance(data, (int, float)):
                balance += float(data)
        logger.info(f"Balance totale pour réinvestissement : {balance} USD")
        
        last_reinvestment = datetime.fromisoformat(strategy_json.get('last_reinvestment', datetime.now().isoformat()))
        if (datetime.now() - last_reinvestment).days >= int(os.getenv('REINVEST_CYCLE_DAYS', 3)):
            strategy_json['roadmap'].append({"asset": "SPY", "alloc": 0.1, "position_type": "buy"})
            strategy_json['last_reinvestment'] = datetime.now().isoformat()
            logger.info("Réinvestissement effectué : ajout SPY à la roadmap")
        return strategy_json
    except Exception as e:
        logger.error(f"Erreur réinvestissement : {str(e)}")
        return strategy_json
