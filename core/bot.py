import os
import json
import asyncio
import logging
import pandas as pd
from datetime import datetime, time
from telegram import Bot
from dotenv import load_dotenv
import sys

# Configurer le logging
logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("Début du script bot.py")

# Vérifier le chemin de kalman_filter.py
try:
    import utils.kalman_filter
    logger.info(f"Chemin de kalman_filter.py : {utils.kalman_filter.__file__}")
except Exception as e:
    logger.error(f"Erreur vérification chemin kalman_filter.py : {str(e)}")

# Vérifier les dépendances
try:
    logger.info("Importation des modules utils")
    from utils.data_fetch import fetch_yahoo_returns, fetch_option_chain
    # Forcer l’importation depuis utils/kalman_filter.py
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from utils.kalman_filter import apply_kalman_filter
    from utils.portfolio_fetch import fetch_portfolio
    from utils.reinvestment_handler import reinvest_gains
    from utils.stat_arb import stat_arb_opportunity
    logger.info("Modules utils importés avec succès")
except Exception as e:
    logger.error(f"Erreur importation modules utils : {str(e)}")
    sys.exit(1)

# Charger les variables d’environnement
try:
    logger.info("Chargement des variables d’environnement")
    load_dotenv()
    logger.info("Variables d’environnement chargées")
except Exception as e:
    logger.error(f"Erreur chargement dotenv : {str(e)}")
    sys.exit(1)

# Vérifier les variables Telegram
try:
    logger.info("Vérification des variables Telegram")
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
    if not telegram_bot_token or not telegram_channel_id:
        logger.error("TELEGRAM_BOT_TOKEN ou TELEGRAM_CHANNEL_ID manquant dans .env")
        raise ValueError("TELEGRAM_BOT_TOKEN ou TELEGRAM_CHANNEL_ID manquant dans .env")
    logger.info(f"Variables Telegram : token={telegram_bot_token[:4]}..., channel_id={telegram_channel_id}")
except Exception as e:
    logger.error(f"Erreur variables Telegram : {str(e)}")
    sys.exit(1)

# Initialiser le bot Telegram
try:
    logger.info("Initialisation du Bot Telegram")
    bot = Bot(token=telegram_bot_token)
    logger.info("Bot Telegram initialisé")
except Exception as e:
    logger.error(f"Erreur initialisation Bot Telegram : {str(e)}")
    sys.exit(1)

async def send_notification(message):
    """Envoie une notification au canal Telegram."""
    try:
        logger.info(f"Envoi notification : {message}")
        await bot.send_message(chat_id=telegram_channel_id, text=message)
        logger.info(f"Notification envoyée : {message}")
    except Exception as e:
        logger.error(f"Erreur envoi notification : {str(e)}")

async def daily_roadmap():
    """Génère la roadmap quotidienne."""
    try:
        logger.info("Début de la génération de la roadmap")
        # Charger les stratégies depuis strategies.json
        with open('strategies.json', 'r') as f:
            strategy_json = json.load(f)
        logger.info(f"strategies.json chargé : {strategy_json}")

        # Récupérer les rendements des actifs
        symbols = ['SPY', 'QQQ', 'IWM', 'AAPL', 'EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'UKOIL', 'NGAS', 'XETHZEUR', 'USDCUSD']
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
            vix = fetch_yahoo_returns('VXX')[-1]  # Utiliser VXX au lieu de ^VIX
            logger.info(f"VXX récupéré : {vix}")
        except Exception as e:
            await bot.send_message(chat_id=telegram_channel_id, text=f"⚠️ Erreur récupération VXX : {str(e)}. Utilisation valeur par défaut.")
            vix = 0.02  # Valeur par défaut (rendement journalier)
            logger.info(f"VXX par défaut : {vix}")

        # Vérifier les seuils Black Swan
        if vix > float(os.getenv('VIX_THRESHOLD_CRITICAL', 0.25)):
            await send_notification("⚠️ Black Swan détecté : rebalancement vers XAUUSD")
            strategy_json['roadmap'] = [{"asset": "XAUUSD", "alloc": 0.5, "position_type": "buy"}]
            logger.info(f"Roadmap Black Swan : {strategy_json['roadmap']}")
            return strategy_json

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

        strategy_json['roadmap'] = roadmap if roadmap else [{"asset": "EURUSD", "alloc": 0.05, "position_type": "buy"}]
        logger.info(f"Roadmap générée : {strategy_json['roadmap']}")
        
        # Réinvestir les gains
        try:
            strategy_json = reinvest_gains(strategy_json)
            logger.info("Réinvestissement réussi")
        except Exception as e:
            await send_notification(f"⚠️ Erreur réinvestissement : {str(e)}. Ignorer réinvestissement.")
            logger.error(f"Erreur réinvestissement : {str(e)}")

        # Envoyer la roadmap via Telegram
        message = (
            f"📊 Roadmap: {json.dumps(strategy_json['roadmap'], indent=2)}\n"
            "📈 Trades simulés (paper trading)\n"
            "⚠️ Aucune garantie de profit, risques élevés (AMF conformité)"
        )
        await send_notification(message)
        logger.info(f"Roadmap envoyée : {strategy_json['roadmap']}")

        # Sauvegarder la roadmap
        with open('strategies.json', 'w') as f:
            json.dump(strategy_json, f, indent=2)
        logger.info("strategies.json sauvegardé")

        return strategy_json
    except Exception as e:
        logger.error(f"Erreur daily_roadmap : {str(e)}")
        await send_notification(f"⚠️ Erreur génération roadmap : {str(e)}")
        return {}

async def main():
    """Boucle principale du bot."""
    logger.info("Démarrage boucle principale")
    try:
        # Forcer l'exécution immédiate pour tester
        await daily_roadmap()
    except Exception as e:
        logger.error(f"Erreur test immédiat daily_roadmap : {str(e)}")
        await send_notification(f"⚠️ Erreur test immédiat : {str(e)}")
    while True:
        try:
            now = datetime.now()
            pre_market_time = time(int(os.getenv('PRE_MARKET_HOUR_UTC', 7)), 0)
            logger.info(f"Heure actuelle : {now}, Heure pré-marché : {pre_market_time}")
            if now.hour == pre_market_time.hour:
                await daily_roadmap()
            await asyncio.sleep(int(os.getenv('SLEEP_CHECK_INTERVAL_HOURS', 1)) * 3600)
        except Exception as e:
            logger.error(f"Erreur boucle principale : {str(e)}")
            await send_notification(f"⚠️ Erreur bot : {str(e)}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    logger.info("Lancement du bot")
    asyncio.run(main())
