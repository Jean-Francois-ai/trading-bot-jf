import os
import logging
import oandapyV20
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.orders as orders
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta

# Configurer le logging
logging.basicConfig(
    filename='oanda_test.log',
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

# Configurer l’API Oanda
try:
    client = oandapyV20.API(
        access_token=os.getenv('OANDA_API_KEY'),
        environment='practice'  # Mode paper trading
    )
    logger.info("Connexion à l’API Oanda réussie.")
except Exception as e:
    logger.error(f"Erreur lors de la connexion à l’API Oanda : {str(e)}")
    raise

def test_get_account():
    """Teste la récupération des informations du compte."""
    try:
        r = accounts.AccountDetails(accountID=os.getenv('OANDA_ACCOUNT_ID'))
        client.request(r)
        account = r.response['account']
        logger.info(f"Solde du compte : {account['balance']} USD")
        logger.info(f"Valeur NAV : {account['NAV']} USD")
        return account
    except Exception as e:
        logger.error(f"Erreur get_account : {str(e)}")
        return None

def test_fetch_instruments():
    """Teste la récupération de la liste des instruments."""
    try:
        r = accounts.AccountInstruments(accountID=os.getenv('OANDA_ACCOUNT_ID'))
        client.request(r)
        instruments_list = r.response['instruments']
        logger.info(f"Instruments disponibles : {[inst['name'] for inst in instruments_list]}")
        return instruments_list
    except Exception as e:
        logger.error(f"Erreur fetch_instruments : {str(e)}")
        return []

def test_get_prices(symbols):
    """Teste la récupération des prix pour une liste de symboles."""
    results = {}
    for symbol in symbols:
        try:
            params = {'instruments': symbol}
            r = pricing.PricingInfo(accountID=os.getenv('OANDA_ACCOUNT_ID'), params=params)
            client.request(r)
            price = r.response['prices'][0]
            close = float(price['closeoutAsk'])
            open_price = float(price['bids'][0]['price'])
            returns = [(close - open_price) / open_price] if open_price != 0 else [0]
            logger.info(f"Prix pour {symbol} : close={close}, open={open_price}, rendement={returns}")
            results[symbol] = returns
        except Exception as e:
            logger.error(f"Erreur get_prices pour {symbol} : {str(e)}")
            results[symbol] = []
    return results

def test_submit_order(symbol, units=1000, side='buy'):
    """Teste la soumission d’un ordre simulé."""
    try:
        order_data = {
            "order": {
                "units": str(units) if side == 'buy' else str(-units),
                "instrument": symbol,
                "timeInForce": "FOK",
                "type": "MARKET",
                "positionFill": "DEFAULT"
            }
        }
        r = orders.OrderCreate(accountID=os.getenv('OANDA_ACCOUNT_ID'), data=order_data)
        client.request(r)
        order = r.response['orderCreateTransaction']
        logger.info(f"Ordre soumis : {symbol}, {units} unités, {side}, ID : {order['id']}")
        return order
    except Exception as e:
        logger.error(f"Erreur submit_order pour {symbol} : {str(e)}")
        return None

def main():
    """Fonction principale pour exécuter les tests."""
    logger.info("Début des tests de l’API Oanda")
    
    # Liste des symboles à tester (valides pour Oanda)
    symbols = ['EUR_USD', 'GBP_USD', 'USD_JPY', 'XAU_USD', 'WTICO_USD', 'NATGAS_USD']
    
    # Test 1 : Informations du compte
    account = test_get_account()
    
    # Test 2 : Liste des instruments
    instruments_list = test_fetch_instruments()
    
    # Test 3 : Prix des instruments
    prices = test_get_prices(symbols)
    
    # Test 4 : Soumettre un ordre simulé (paper trading)
    order = test_submit_order('EUR_USD', units=1000, side='buy')
    
    logger.info("Fin des tests de l’API Oanda")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Erreur principale : {str(e)}")
        
