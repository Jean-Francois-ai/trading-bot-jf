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
        # Vérifier si les données sont valides
        if not isinstance(data, (list, np.ndarray)) or len(data) == 0:
            logger.warning("Données vides ou invalides pour le filtre de Kalman")
            return [0]

        # Convertir les données en numpy array
        data = np.array(data, dtype=float)

        # Paramètres du filtre de Kalman
        n_iter = len(data)
        sz = (n_iter,)  # Taille des observations
        z = data  # Observations (rendements)

        # Initialisation des matrices
        Q = 1e-5  # Bruit du processus
        R = 0.1   # Bruit de mesure
        xhat = np.zeros(sz)  # Estimation filtrée
        P = np.ones(sz)     # Covariance de l’erreur
        xhatminus = np.zeros(sz)  # Estimation prédite
        Pminus = np.ones(sz)      # Covariance prédite
        K = np.zeros(sz)          # Gain de Kalman

        xhat[0] = z[0]
        P[0] = 1.0

        # Boucle du filtre de Kalman
        for k in range(1, n_iter):
            # Prédiction
            xhatminus[k] = xhat[k-1]
            Pminus[k] = P[k-1] + Q

            # Mise à jour
            K[k] = Pminus[k] / (Pminus[k] + R)
            xhat[k] = xhatminus[k] + K[k] * (z[k] - xhatminus[k])
            P[k] = (1 - K[k]) * Pminus[k]

        logger.info(f"Filtre de Kalman appliqué : {xhat.tolist()}")
        return xhat.tolist()
    except Exception as e:
        logger.error(f"Erreur apply_kalman_filter : {str(e)}")
        return [0]
