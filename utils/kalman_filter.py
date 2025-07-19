import numpy as np
import logging
import ccxt.async_support as ccxt
import os
from dotenv import load_dotenv

# Configurer le logging
logging.basicConfig(
    filename='logs/kalman_filter.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

async def fetch_historical_data(symbol, timeframe='1h', limit=100):
    """Récupère les données historiques pour le filtre de Kalman."""
    try:
        binance = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'apiSecret': os.getenv('BINANCE_API_SECRET'),
            'enableRateLimit': True
        })
        ohlcv = await binance.fetch_ohlcv(symbol, timeframe, limit=limit)
        await binance.close()
        returns = [(ohlcv[i][4] - ohlcv[i][1]) / ohlcv[i][1] for i in range(len(ohlcv)) if ohlcv[i][1] != 0]
        logger.info(f"Données historiques pour {symbol} : {returns}")
        return returns
    except Exception as e:
        logger.error(f"Erreur récupération données historiques pour {symbol} : {str(e)}")
        return [0.0]

def apply_kalman_filter(data):
    """Applique un filtre de Kalman sur les données de rendement."""
    try:
        if not data or len(data) < 2:
            logger.warning("Données insuffisantes pour le filtre de Kalman, retour direct")
            return [0.0]
        
        data = np.array(data, dtype=float)
        n_iter = len(data)
        sz = (n_iter,)
        Q = 1e-5  # Bruit du processus
        xhat = np.zeros(sz)  # Estimation filtrée
        P = np.zeros(sz)  # Covariance de l'erreur
        xhatminus = np.zeros(sz)  # Estimation prédite
        Pminus = np.zeros(sz)  # Covariance prédite
        K = np.zeros(sz)  # Gain de Kalman
        R = 0.1 ** 2  # Bruit de mesure

        xhat[0] = data[0]
        P[0] = 1.0

        for k in range(1, n_iter):
            xhatminus[k] = xhat[k-1]
            Pminus[k] = P[k-1] + Q
            K[k] = Pminus[k] / (Pminus[k] + R)
            xhat[k] = xhatminus[k] + K[k] * (data[k] - xhatminus[k])
            P[k] = (1 - K[k]) * Pminus[k]

        filtered = xhat.tolist()
        logger.info(f"Filtre de Kalman appliqué : {filtered}")
        return filtered
    except Exception as e:
        logger.error(f"Erreur application filtre Kalman : {str(e)}")
        return [0.0]
