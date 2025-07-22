import os
import requests
import json
from dotenv import load_dotenv
import logging

# Configurer le logging
logging.basicConfig(
    filename='logs/openrouter_client.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

def get_deepseek_advice(roadmap, kalman_returns):
    """Récupère des conseils d'allocation via DeepSeek sur OpenRouter."""
    try:
        openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        if not openrouter_api_key:
            logger.error("Clé API OpenRouter manquante")
            return "Erreur : Clé API OpenRouter non configurée"

        # Préparer les données pour l'API
        prompt = f"Analyse cette roadmap : {json.dumps(roadmap, indent=2)}\nRendements Kalman : {json.dumps(kalman_returns, indent=2)}\nFournis des conseils d'allocation optimisés pour Binance, Alpaca, Kraken, Oanda."
        headers = {
            "Authorization": f"Bearer {openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Jean-Francois-ai/trading-bot-jf",
            "X-Title": "Trading Bot JF"
        }
        data = {
            "model": "deepseek/deepseek-r1:free",  # Modèle valide
            "messages": [{"role": "user", "content": prompt}]
        }

        # Appeler l'API OpenRouter
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        logger.info(f"Requête HTTP : POST https://openrouter.ai/api/v1/chat/completions \"{response.status_code}\"")
        
        if response.status_code == 200:
            advice = response.json()['choices'][0]['message']['content']
            logger.info(f"Conseils DeepSeek reçus : {advice}")
            return advice
        else:
            logger.error(f"Échec requête OpenRouter : {response.text}")
            return f"Erreur API : {response.text}"
    except Exception as e:
        logger.error(f"Erreur get_deepseek_advice : {str(e)}")
        return f"Erreur : {str(e)}"
