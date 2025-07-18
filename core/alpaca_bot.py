import os
import json
import asyncio
import logging
import pandas as pd
from datetime import datetime, time
from dotenv import load_dotenv
import sys

# Configurer le logging
logging.basicConfig(
    filename='alpaca_bot.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("Démarrage du script alpaca_bot.py")

# Forcer l’importation depuis utils/kalman_filter.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.data_fetch import fetch_yahoo_returns, fetch_option_chain
from utils.kalman_filter import apply_kalman_filter
from utils.stat_arb import stat_arb_opportunity

async def alpaca_roadmap():
    """Génère la roadmap pour Alpaca."""
    try:
        logger.info("Début de la génération de la roadmap Alpaca")
        # Charger les stratégies depuis strategies.json
        with open('strategies.json', 'r') as f:
            strategy_json = json.load(f)
        logger.info(f"strategies.json chargé : {strategy_json}")

        # Récupérer les rendements des actifs Alpaca
        symbols = ['SPY', 'QQQ', 'IWM', 'AAPL']
        returns = {}
        for symbol in symbols:
            try:
                returns[symbol] = fetch_yahoo_returns(symbol)
                logger.info(f"Rendements récupérés pour {symbol} : {returns[symbol]}")
            except Exception as e:
                logger.error(f"Erreur récupération rendements pour {symbol} : {str(e)}")
                returns[symbol] = [0]

        # Appliquer le filtre de Kalman
        kalman_returns = {}
        for symbol, data in returns.items():
            try:
                kalman_returns[symbol] = apply_kalman_filter(data)
                logger.info(f"Rendements Kalman pour {symbol} : {kalman_returns[symbol]}")
            except Exception as e:
                logger.error(f"Erreur Kalman pour {symbol} : {str(e)}")
                kalman_returns[symbol] = [0]

        # Vérifier la volatilité (VXX)
        try:
            vix = fetch_yahoo_returns('VXX')[-1]
            logger.info(f"VXX récupéré : {vix}")
        except Exception as e:
            logger.error(f"Erreur récupération VXX : {str(e)}")
            vix = 0.02
            logger.info(f"VXX par défaut : {vix}")

        # Vérifier les seuils Black Swan
        if vix > float(os.getenv('VIX_THRESHOLD_CRITICAL', 0.25)):
            logger.info("Black Swan détecté : rebalancement vers XAUUSD")
            roadmap = [{"asset": "XAUUSD", "alloc": 0.5, "position_type": "buy"}]
            return roadmap

        # Générer la roadmap
        roadmap = []
        for symbol in symbols:
            try:
                if symbol in kalman_returns and len(kalman_returns[symbol]) > 0:
                    alloc = stat_arb_opportunity(symbol, kalman_returns[symbol], fetch_option_chain(symbol))
                    if alloc:
                        roadmap.append(alloc)
                        logger.info(f"Allocation ajoutée pour {symbol} : {alloc}")
                    else:
                        logger.info(f"Aucune allocation pour {symbol}")
            except Exception as e:
                logger.error(f"Erreur stat_arb_opportunity pour {symbol} : {str(e)}")

        # Sauvegarder la roadmap partielle
        with open('roadmaps/alpaca_roadmap.json', 'w') as f:
            json.dump(roadmap, f, indent=2)
        logger.info(f"Roadmap Alpaca sauvegardée : {roadmap}")
        return roadmap
    except Exception as e:
        logger.error(f"Erreur alpaca_roadmap : {str(e)}")
        return []

async def main():
    """Boucle principale du bot Alpaca."""
    logger.info("Démarrage boucle principale")
    try:
        await alpaca_roadmap()
    except Exception as e:
        logger.error(f"Erreur test immédiat alpaca_roadmap : {str(e)}")
    while True:
        try:
            now = datetime.now()
            pre_market_time = time(int(os.getenv('PRE_MARKET_HOUR_UTC', 7)), 0)
            logger.info(f"Heure actuelle : {now}, Heure pré-marché : {pre_market_time}")
            if now.hour == pre_market_time.hour:
                await alpaca_roadmap()
            await asyncio.sleep(int(os.getenv('SLEEP_CHECK_INTERVAL_HOURS', 1)) * 3600)
        except Exception as e:
            logger.error(f"Erreur boucle principale : {str(e)}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    logger.info("Lancement du bot Alpaca")
    asyncio.run(main())
