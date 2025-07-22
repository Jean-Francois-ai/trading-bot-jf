import os
import json
import asyncio
import logging
from datetime import datetime, time
import requests
from dotenv import load_dotenv
import sys

# Configurer le logging
logging.basicConfig(
    filename='logs/supervisor_bot.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("Démarrage du script supervisor_bot.py")

# Forcer l’importation depuis utils/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.openrouter_client import get_deepseek_advice

async def supervisor_roadmap():
    """Consolide les roadmaps et envoie des notifications."""
    try:
        logger.info("Début de la consolidation des roadmaps")
<<<<<<< HEAD
        now = datetime.now()
        is_weekend = now.weekday() >= 5
        roadmap_files = [
            'roadmaps/binance_roadmap.json',
            'roadmaps/alpaca_roadmap.json',
            'roadmaps/kraken_roadmap.json',
            'roadmaps/oanda_roadmap.json'
        ]
        roadmap = []
        kalman_returns = {}
        errors = []

        # Lire les roadmaps partielles
        for file in roadmap_files:
            try:
                with open(file, 'r') as f:
                    partial_roadmap = json.load(f)
                    roadmap.extend(partial_roadmap)
                    logger.info(f"Roadmap partielle chargée depuis {file}: {partial_roadmap}")
            except Exception as e:
                logger.error(f"Erreur lecture {file}: {str(e)}")
                errors.append(f"Erreur lecture {file}: {str(e)}")

        # Collecter les rendements Kalman depuis les logs
        log_files = ['logs/binance_bot.log', 'logs/alpaca_bot.log', 'logs/kraken_bot.log', 'logs/oanda_bot.log']
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    log_content = f.readlines()
                    for line in log_content:
                        if "Rendements Kalman pour" in line:
                            parts = line.split("Rendements Kalman pour ")
                            if len(parts) > 1:
                                symbol, data = parts[1].split(" : ")
                                kalman_returns[symbol.strip()] = json.loads(data.strip())
                        if "ERROR" in line:
                            errors.append(f"Erreurs détectées dans {log_file}: {line.strip()}")
            except Exception as e:
                logger.error(f"Erreur lecture {log_file}: {str(e)}")
                errors.append(f"Erreur lecture {log_file}: {str(e)}")

        # Charger les stratégies
        with open('strategies.json', 'r') as f:
            strategy_json = json.load(f)
        strategy_json['roadmap'] = roadmap if roadmap else strategy_json['roadmap']
        logger.info(f"Roadmap consolidée : {strategy_json['roadmap']}")
=======
        # Charger les stratégies depuis strategies.json
        with open('strategies.json', 'r') as f:
            strategy_json = json.load(f)
        logger.info(f"strategies.json chargé : {strategy_json}")

        # Charger la roadmap Binance
        roadmap = []
        try:
            with open('roadmaps/binance_roadmap.json', 'r') as f:
                roadmap = json.load(f)
            logger.info(f"Roadmap partielle chargée depuis roadmaps/binance_roadmap.json: {roadmap}")
        except Exception as e:
            logger.error(f"Erreur lecture roadmaps/binance_roadmap.json: {str(e)}")
            roadmap = []

        # Consolider la roadmap
        consolidated_roadmap = roadmap
        logger.info(f"Roadmap consolidée : {consolidated_roadmap}")

        # Obtenir des conseils DeepSeek
        kalman_returns = {item['asset']: [0.0] for item in strategy_json['roadmap']}  # Placeholder
        try:
            with open('logs/binance_bot.log', 'r') as f:
                log_content = f.readlines()
                for line in log_content:
                    if "Rendements Kalman pour" in line:
                        parts = line.split("Rendements Kalman pour ")
                        if len(parts) > 1:
                            symbol, data = parts[1].split(" : ")
                            kalman_returns[symbol.strip()] = json.loads(data.strip())
        except Exception as e:
            logger.error(f"Erreur lecture binance_bot.log: {str(e)}")
>>>>>>> 38e4a76c1166096bcddb85580f070c9817da5761

        advice = get_deepseek_advice(strategy_json['roadmap'], kalman_returns)
        logger.info(f"Conseils DeepSeek reçus : {advice}")
        logger.info(f"Conseils DeepSeek intégrés : {advice}")

<<<<<<< HEAD
        # Réinvestir les gains
        from utils.reinvestment_handler import reinvest_gains
        try:
            strategy_json = reinvest_gains(strategy_json)
            logger.info("Réinvestissement réussi")
        except Exception as e:
            errors.append(f"Erreur réinvestissement : {str(e)}")
            logger.error(f"Erreur réinvestissement : {str(e)}")

        # Sauvegarder la roadmap consolidée
        with open('strategies.json', 'w') as f:
            json.dump(strategy_json, f, indent=2)
        logger.info("strategies.json sauvegardé")

        # Envoyer la notification Telegram
        message = (
            f"📊 Roadmap: {json.dumps(strategy_json['roadmap'], indent=2)}\n"
            f"💡 Conseils DeepSeek : {advice}\n"
            f"📈 Trades réels (Binance, Alpaca, Kraken, Oanda)\n"
        )
        if is_weekend:
            message += "🔔 Week-end : seuls les cryptos (Binance, Kraken) sont actifs\n"
        if errors:
            message += f"⚠️ Erreurs détectées : {'; '.join(errors)}\n"
        message += "⚠️ Aucune garantie de profit, risques élevés (AMF conformité)"
        await send_notification(message)
=======
        # Envoyer une notification Telegram
        telegram_message = (
            f"🔔 Roadmap consolidée : {json.dumps(consolidated_roadmap, indent=2)}\n\n"
            f"📝 Conseils DeepSeek : {advice}\n\n"
            f"⚠️ Les performances passées ne garantissent pas les résultats futurs (conformité AMF)."
        )
        if datetime.now().weekday() >= 5:
            telegram_message += "\n🔔 Week-end : seuls les cryptos (Binance) sont actifs."
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage",
                json={
                    'chat_id': os.getenv('TELEGRAM_CHANNEL_ID'),
                    'text': telegram_message
                }
            )
            logger.info(f"HTTP Request: POST https://api.telegram.org/botREDACTED/sendMessage \"{response.status_code}\"")
            if response.status_code == 200:
                logger.info(f"Notification envoyée : {telegram_message}")
            else:
                logger.error(f"Échec envoi notification : {response.text}")
        except Exception as e:
            logger.error(f"Erreur envoi notification : {str(e)}")
>>>>>>> 38e4a76c1166096bcddb85580f070c9817da5761

        return consolidated_roadmap
    except Exception as e:
        logger.error(f"Erreur supervisor_roadmap : {str(e)}")
        telegram_message = f"⚠️ Erreur génération roadmap : {str(e)}"
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage",
                json={
                    'chat_id': os.getenv('TELEGRAM_CHANNEL_ID'),
                    'text': telegram_message
                }
            )
            logger.info(f"HTTP Request: POST https://api.telegram.org/botREDACTED/sendMessage \"{response.status_code}\"")
            if response.status_code == 200:
                logger.info(f"Notification envoyée : {telegram_message}")
            else:
                logger.error(f"Échec envoi notification : {response.text}")
        except Exception as e:
            logger.error(f"Erreur envoi notification : {str(e)}")
        return []

async def main():
    """Boucle principale du bot de supervision."""
    logger.info("Démarrage boucle principale")
    try:
        await supervisor_roadmap()
    except Exception as e:
        logger.error(f"Erreur test immédiat supervisor_roadmap : {str(e)}")
    while True:
        try:
            now = datetime.now()
            pre_market_time = time(int(os.getenv('PRE_MARKET_HOUR_UTC', 7)), 5)
            logger.info(f"Heure actuelle : {now}, Heure pré-marché : {pre_market_time}")
            if now.weekday() >= 5:  # Week-end, toujours actif pour cryptos
                await supervisor_roadmap()
            elif now.hour == pre_market_time.hour:
                await supervisor_roadmap()
            await asyncio.sleep(int(os.getenv('SLEEP_CHECK_INTERVAL_HOURS', 1)) * 3600)
        except Exception as e:
            logger.error(f"Erreur boucle principale : {str(e)}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    logger.info("Lancement du bot de supervision")
    asyncio.run(main())
