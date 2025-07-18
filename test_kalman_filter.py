import numpy as np
import logging
from utils.kalman_filter import apply_kalman_filter

# Configurer le logging
logging.basicConfig(
    filename='test_kalman_filter.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def test_kalman_filter():
    """Teste apply_kalman_filter avec des données de SPY."""
    try:
        # Données de rendements SPY (extraites de bot.log)
        spy_returns = [-0.00054779, 0.00599671, 0.00282024, -0.00351539, 0.00190821, -0.0042733, 0.0033433]
        result = apply_kalman_filter(spy_returns)
        logger.info(f"Résultat du filtre de Kalman pour SPY : {result}")
    except Exception as e:
        logger.error(f"Erreur test Kalman : {str(e)}")

if __name__ == '__main__':
    logger.info("Lancement du test Kalman")
    test_kalman_filter()
