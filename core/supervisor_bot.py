import os
import json
import asyncio
import logging
from datetime import datetime, time
from telegram import Bot
from dotenv import load_dotenv

# Configurer le logging
logging.basicConfig(
    filename='supervisor_bot.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logger.info("Démarrage du script supervisor_bot.py")

# Charger les variables d’environnement
load_dotenv()
telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
telegram_channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
bot = Bot(token=telegram_bot_token)

async def send_notification(message):
    """Envoie une notification au canal Telegram."""
    try:
        logger.info(f"Envoi notification : {message}")
        await bot.send_message(chat_id=telegram_channel_id, text=message)
        logger.info(f"Notification envoyée : {message}")
    except Exception as e:
        logger.error(f"Erreur envoi notification : {str(e)}")

async def supervisor_roadmap():
    """Consolide les roadmaps partielles et envoie la notification."""
    try:
        logger.info("Début de la consolidation des roadmaps")
        now = datetime.now()
        is_weekend = now.weekday() >= 5
        roadmap_files = ['roadmaps/binance_roadmap.json']
        roadmap = []
        kalman_returns = {}
        errors = []

        # Lire les roadmaps partielles (Binance uniquement)
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
        log_files = ['binance_bot.log']
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
        strategy_json['roadmap'] = roadmap if roadmap else [{"asset": "ETH/EUR", "alloc": 0.05, "position_type": "buy"}]
        logger.info(f"Roadmap consolidée : {strategy_json['roadmap']}")

        # Consulter DeepSeek via OpenRouter
        from utils.openrouter_client import get_deepseek_advice
        advice = get_deepseek_advice(strategy_json['roadmap'], kalman_returns)
        logger.info(f"Conseils DeepSeek intégrés : {advice}")

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
            "📈 Trades réels (Binance)\n"
        )
        if is_weekend:
            message += "🔔 Week-end : seuls les cryptos (Binance) sont actifs\n"
        if errors:
            message += f"⚠️ Erreurs détectées : {'; '.join(errors)}\n"
        message += "⚠️ Aucune garantie de profit, risques élevés (AMF conformité)"
        await send_notification(message)

        return strategy_json
    except Exception as e:
        logger.error(f"Erreur supervisor_roadmap : {str(e)}")
        await send_notification(f"⚠️ Erreur génération roadmap : {str(e)}")
        return {}

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
            if now.weekday() >= 5 or (now.hour == pre_market_time.hour and now.minute >= pre_market_time.minute):
                await supervisor_roadmap()
            await asyncio.sleep(int(os.getenv('SLEEP_CHECK_INTERVAL_HOURS', 1)) * 3600)
        except Exception as e:
            logger.error(f"Erreur boucle principale : {str(e)}")
            await send_notification(f"⚠️ Erreur bot supervision : {str(e)}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    logger.info("Lancement du bot de supervision")
    asyncio.run(main())
