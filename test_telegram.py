import os
import asyncio
import logging
from telegram import Bot
from dotenv import load_dotenv

# Configurer le logging
logging.basicConfig(
    filename='telegram_test.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

async def test_telegram():
    """Teste la connexion Telegram."""
    try:
        logger.info("Début test Telegram")
        telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
        if not telegram_bot_token or not telegram_channel_id:
            logger.error("TELEGRAM_BOT_TOKEN ou TELEGRAM_CHANNEL_ID manquant dans .env")
            raise ValueError("TELEGRAM_BOT_TOKEN ou TELEGRAM_CHANNEL_ID manquant dans .env")
        logger.info(f"Variables Telegram : token={telegram_bot_token[:4]}..., channel_id={telegram_channel_id}")
        
        bot = Bot(token=telegram_bot_token)
        logger.info("Bot Telegram initialisé")
        
        await bot.send_message(chat_id=telegram_channel_id, text="Test de connexion Telegram réussi !")
        logger.info("Message de test envoyé")
    except Exception as e:
        logger.error(f"Erreur test Telegram : {str(e)}")

if __name__ == '__main__':
    logger.info("Lancement test Telegram")
    asyncio.run(test_telegram())
