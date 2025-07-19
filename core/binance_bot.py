import os
import json
import asyncio
import logging
from datetime import datetime, time
from dotenv import load_dotenv
import sys

# Configurer le logging
logging.basicConfig(
    filename='binance_bot.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("Démarrage du script binance_bot.py")

# Forcer l’importation depuis utils/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.binance_client import fetch_binance_prices, submit_binance_order
from utils.kalman_filter import apply_kalman_filter
from utils.stat_arb import stat_arb_opportunity

async def binance_roadmap():
    """Génère la roadmap pour Binance (compte réel)."""
    try:
        logger.info("Début de la génération de la roadmap Binance")
        # Charger les stratégies depuis strategies.json
        with open('strategies.json', 'r') as f:
            strategy_json = json.load(f)
        logger.info(f"strategies.json chargé : {strategy_json}")

        # Récupérer les symboles depuis strategies.json
        symbols = [item['asset'] for item in strategy_json['roadmap']]
        logger.info(f"Symboles chargés : {symbols}")

        # Récupérer les rendements des actifs Binance
        returns = {}
        for symbol in symbols:
            try:
                returns[symbol] = await fetch_binance_prices(symbol)
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

        # Générer la roadmap
        roadmap = []
        for symbol in symbols:
            try:
                if kalman_returns[symbol] and len(kalman_returns[symbol]) > 0 and kalman_returns[symbol][-1] > 0:
                    alloc = stat_arb_opportunity(symbol, kalman_returns[symbol], None)
                    if alloc:
                        roadmap.append(alloc)
                        logger.info(f"Allocation ajoutée pour {symbol} : {alloc}")
                        # Passer un ordre réel (commenté pour tests)
                        # order = await submit_binance_order(symbol, alloc['alloc'], alloc['position_type'])
                        # if order:
                        #     logger.info(f"Ordre réel passé pour {symbol} : {order}")
                        # else:
                        #     logger.error(f"Échec passage ordre pour {symbol}")
                    else:
                        logger.info(f"Aucune allocation pour {symbol}")
            except Exception as e:
                logger.error(f"Erreur stat_arb_opportunity pour {symbol} : {str(e)}")

        # Sauvegarder la roadmap partielle
        with open('roadmaps/binance_roadmap.json', 'w') as f:
            json.dump(roadmap, f, indent=2)
        logger.info(f"Roadmap Binance sauvegardée : {roadmap}")
        return roadmap
    except Exception as e:
        logger.error(f"Erreur binance_roadmap : {str(e)}")
        return []

async def main():
    """Boucle principale du bot Binance."""
    logger.info("Démarrage boucle principale")
    try:
        await binance_roadmap()
    except Exception as e:
        logger.error(f"Erreur test immédiat binance_roadmap : {str(e)}")
    while True:
        try:
            now = datetime.now()
            pre_market_time = time(int(os.getenv('PRE_MARKET_HOUR_UTC', 7)), 0)
            logger.info(f"Heure actuelle : {now}, Heure pré-marché : {pre_market_time}")
            if now.weekday() >= 5:  # Week-end, toujours actif pour cryptos
                await binance_roadmap()
            elif now.hour == pre_market_time.hour:
                await binance_roadmap()
            await asyncio.sleep(int(os.getenv('SLEEP_CHECK_INTERVAL_HOURS', 1)) * 3600)
        except Exception as e:
            logger.error(f"Erreur boucle principale : {str(e)}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    logger.info("Lancement du bot Binance")
    asyncio.run(main())
