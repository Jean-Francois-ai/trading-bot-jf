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
    """Applique un filtre de Kalman pour lisser les rendements."""
    try:
        if not data or len(data) == 0:
            logger.error("Données vides ou invalides pour le filtre de Kalman")
            return [0]

        # Paramètres du filtre de Kalman
        n_iter = len(data)
        sz = (n_iter,)  # Taille du tableau
        Q = 1e-5  # Bruit du processus
        R = 0.1  # Bruit de mesure
        xhat = np.zeros(sz)  # Estimation filtrée
        P = np.zeros(sz)  # Covariance de l'erreur
        xhatminus = np.zeros(sz)  # Estimation prédite
        Pminus = np.zeros(sz)  # Covariance prédite
        K = np.zeros(sz)  # Gain de Kalman
        xhat[0] = data[0]
        P[0] = 1.0

        for k in range(1, n_iter):
            # Prédiction
            xhatminus[k] = xhat[k-1]
            Pminus[k] = P[k-1] + Q
            # Mise à jour
            K[k] = Pminus[k] / (Pminus[k] + R)
            xhat[k] = xhatminus[k] + K[k] * (data[k] - xhatminus[k])
            P[k] = (1 - K[k]) * Pminus[k]

        logger.info(f"Filtre de Kalman appliqué : {xhat.tolist()}")
        return xhat.tolist()
    except Exception as e:
        logger.error(f"Erreur application filtre de Kalman : {str(e)}")
        return [0]
