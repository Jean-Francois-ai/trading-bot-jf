import os
import logging
import krakenex
from dotenv import load_dotenv
import pandas as pd

# Configurer le logging
logging.basicConfig(
    filename='kraken_test.log',
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

# Configurer l’API Kraken
try:
    k = krakenex.API(key=os.getenv('KRAKEN_API_KEY'), secret=os.getenv('KRAKEN_SECRET_KEY'))
    logger.info("Connexion à l’API Kraken réussie.")
except Exception as e:
    logger.error(f"Erreur lors de la connexion à l’API Kraken : {str(e)}")
    raise

def test_get_account():
    """Teste la récupération des informations du compte."""
    try:
        balance = k.query_private('Balance')['result']
        logger.info(f"Solde du compte : {balance}")
        return balance
    except Exception as e:
        logger.error(f"Erreur get_account : {str(e)}")
        return None

def test_fetch_pairs():
    """Teste la récupération des paires disponibles."""
    try:
        pairs = k.query_public('AssetPairs')['result']
        logger.info(f"Paires disponibles : {list(pairs.keys())}")
        return pairs
    except Exception as e:
        logger.error(f"Erreur fetch_pairs : {str(e)}")
        return []

def test_get_prices(symbols):
    """Teste la récupération des prix pour une liste de symboles."""
    results = {}
    for symbol in symbols:
        try:
            ticker = k.query_public('Ticker', {'pair': symbol})['result'][symbol]
            close = float(ticker['c'][0])
            open_price = float(ticker['o'])
            returns = [(close - open_price) / open_price] if open_price != 0 else [0]
            logger.info(f"Prix pour {symbol} : close={close}, open={open_price}, rendement={returns}")
            results[symbol] = returns
        except Exception as e:
            logger.error(f"Erreur get_prices pour {symbol} : {str(e)}")
            results[symbol] = []
    return results

def main():
    """Fonction principale pour exécuter les tests."""
    logger.info("Début des tests de l’API Kraken")
    
    # Liste des symboles à tester (valides pour Kraken)
    symbols = ['XETHZEUR', 'USDCUSD']
    
    # Test 1 : Informations du compte
    account = test_get_account()
    
    # Test 2 : Paires disponibles
    pairs = test_fetch_pairs()
    
    # Test 3 : Prix des paires
    prices = test_get_prices(symbols)
    
    logger.info("Fin des tests de l’API Kraken")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Erreur principale : {str(e)}")
