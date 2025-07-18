from dotenv import load_dotenv
import os
import numpy as np
from sklearn.decomposition import PCA
from utils.data_fetch import fetch_yahoo_returns
load_dotenv()

def pca_correlation(symbols, portfolio):
    """
    Analyse PCA pour détecter les corrélations.
    """
    try:
        data = np.array([fetch_yahoo_returns(symbol) for symbol in symbols]).T
        if data.shape[1] < 2 or data.shape[0] < 2:
            return {'correlated': False, 'explained_variance': 0}
        pca = PCA(n_components=min(data.shape[1], 2))
        pca.fit(data)
        explained_variance = pca.explained_variance_ratio_[0]
        return {'correlated': explained_variance > float(os.getenv('CORRELATION_THRESHOLD', 0.7)), 'explained_variance': explained_variance}
    except Exception as e:
        print(f"Erreur PCA : {str(e)}")
        return {'correlated': False, 'explained_variance': 0}
