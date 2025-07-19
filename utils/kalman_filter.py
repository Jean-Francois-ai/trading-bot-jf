import numpy as np
import logging

# Configurer le logging
logging.basicConfig(
    filename='kalman_filter.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def apply_kalman_filter(data):
    """Applique un filtre de Kalman aux données de rendements."""
    try:
        if not data or len(data) == 0:
            logger.error("Données vides ou invalides pour le filtre de Kalman")
            return [0]
        data = np.array(data, dtype=float)
        n = len(data)
        if n < 2:
            logger.warning("Données insuffisantes pour le filtre de Kalman, retour direct")
            return list(data)

        # Paramètres du filtre de Kalman
        x = np.zeros(n)  # État estimé
        P = np.ones(n)  # Variance de l'estimation
        Q = 0.01  # Variance du bruit de processus
        R = 0.1   # Variance du bruit de mesure

        x[0] = data[0]
        for t in range(1, n):
            # Prédiction
            x_pred = x[t-1]
            P_pred = P[t-1] + Q

            # Mise à jour
            K = P_pred / (P_pred + R)  # Gain de Kalman
            x[t] = x_pred + K * (data[t] - x_pred)
            P[t] = (1 - K) * P_pred

        logger.info(f"Filtre de Kalman appliqué : {list(x)}")
        return list(x)
    except Exception as e:
        logger.error(f"Erreur application filtre de Kalman : {str(e)}")
        return [0]
