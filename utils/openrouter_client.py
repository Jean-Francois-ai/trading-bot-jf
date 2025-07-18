import os
import requests
import logging
from dotenv import load_dotenv

# Configurer le logging
logging.basicConfig(
    filename='openrouter_client.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

def get_deepseek_advice(roadmap, kalman_returns):
    """Consulte DeepSeek via OpenRouter pour des conseils."""
    try:
        if not OPENROUTER_API_KEY:
            logger.error("OPENROUTER_API_KEY manquant dans .env")
            return "Erreur : clé API OpenRouter manquante"

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "deepseek/deepseek-r1:free",
            "messages": [
                {"role": "user", "content": f"Donne des conseils de trading basés sur cette roadmap : {roadmap} et ces rendements Kalman : {kalman_returns}"}
            ]
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        advice = response.json()['choices'][0]['message']['content']
        logger.info(f"Conseils DeepSeek reçus : {advice}")
        return advice
    except Exception as e:
        logger.error(f"Erreur consultation DeepSeek : {str(e)}")
        return f"Erreur consultation DeepSeek : {str(e)}"
