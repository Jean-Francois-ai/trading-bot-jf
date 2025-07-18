import os
import logging
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta

# Configurer le logging
logging.basicConfig(
    filename='alpaca_test.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# Ajouter un handler pour afficher dans le terminal
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logger.addHandler(console)

# Charger les variables d’environnement
load_dotenv()

# Configurer l’API Alpaca
try:
    api = tradeapi.REST(
        key_id=os.getenv('ALPACA_API_KEY'),
        secret_key=os.getenv('ALPACA_SECRET_KEY'),
        base_url=os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),
        api_version='v2'
    )
    logger.info("Connexion à l’API Alpaca réussie.")
except Exception as e:
    logger.error(f"Erreur lors de la connexion à l’API Alpaca : {str(e)}")
    raise

def test_get_account():
    """Teste la récupération des informations du compte."""
    try:
        account = api.get_account()
        logger.info(f"Solde du compte : {account.cash} USD")
        logger.info(f"Valeur du portefeuille : {account.portfolio_value} USD")
        return account
    except Exception as e:
        logger.error(f"Erreur get_account : {str(e)}")
        return None

def test_get_bars(symbols):
    """Teste la récupération des données historiques pour une liste de symboles."""
    results = {}
    end_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')  # Exclure jour en cours
    start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')  # 10 jours
    for symbol in symbols:
        try:
            bars = api.get_bars(symbol, '1D', start=start_date, end=end_date).df
            logger.info(f"Données brutes pour {symbol} : {bars}")
            if not bars.empty and len(bars['close']) >= 2:
                returns = bars['close'].pct_change().dropna().values
                logger.info(f"Rendements pour {symbol} : {returns}")
                results[symbol] = returns
            else:
                logger.warning(f"Données insuffisantes pour {symbol} : {len(bars['close'])} jour(s)")
                results[symbol] = []
        except Exception as e:
            logger.error(f"Erreur get_bars pour {symbol} : {str(e)}")
            if "subscription does not permit" in str(e).lower():
                logger.warning(f"Erreur SIP pour {symbol} : essayer une période plus ancienne")
                try:
                    # Essayer une période plus ancienne
                    older_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                    older_end = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
                    bars = api.get_bars(symbol, '1D', start=older_start, end=older_end).df
                    logger.info(f"Données brutes (période ancienne) pour {symbol} : {bars}")
                    if not bars.empty and len(bars['close']) >= 2:
                        returns = bars['close'].pct_change().dropna().values
                        logger.info(f"Rendements (période ancienne) pour {symbol} : {returns}")
                        results[symbol] = returns
                    else:
                        logger.warning(f"Données insuffisantes (période ancienne) pour {symbol} : {len(bars['close'])} jour(s)")
                        results[symbol] = []
                except Exception as e2:
                    logger.error(f"Erreur get_bars (période ancienne) pour {symbol} : {str(e2)}")
                    results[symbol] = []
            else:
                results[symbol] = []
    return results

def test_list_positions():
    """Teste la récupération des positions du portefeuille."""
    try:
        positions = api.list_positions()
        for position in positions:
            logger.info(f"Position : {position.symbol}, Quantité : {position.qty}, Valeur : {position.market_value}")
        return positions
    except Exception as e:
        logger.error(f"Erreur list_positions : {str(e)}")
        return []

def test_submit_order(symbol, qty=1, side='buy', order_type='market', time_in_force='day'):
    """Teste la soumission d’un ordre simulé."""
    try:
        order = api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=order_type,
            time_in_force=time_in_force
        )
        logger.info(f"Ordre soumis : {symbol}, {qty} unités, {side}, {order_type}, ID : {order.id}")
        return order
    except Exception as e:
        logger.error(f"Erreur submit_order pour {symbol} : {str(e)}")
        return None

def main():
    """Fonction principale pour exécuter les tests."""
    logger.info("Début des tests de l’API Alpaca")
    
    # Liste des symboles à tester (valides pour Alpaca)
    symbols = ['SPY', 'QQQ', 'IWM', 'AAPL', 'VXX']
    
    # Test 1 : Informations du compte
    account = test_get_account()
    
    # Test 2 : Données historiques
    bars = test_get_bars(symbols)
    
    # Test 3 : Positions du portefeuille
    positions = test_list_positions()
    
    # Test 4 : Soumettre un ordre simulé (paper trading)
    order = test_submit_order('SPY', qty=1, side='buy')
    
    logger.info("Fin des tests de l’API Alpaca")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Erreur principale : {str(e)}")
