from dotenv import load_dotenv
import os
import numpy as np
from utils.data_fetch import fetch_yahoo_returns
load_dotenv()

def stress_test_portfolio(portfolio, symbols):
    """
    Effectue un test de stress sur le portefeuille.
    """
    try:
        portfolio_value = sum(p['balance'] for p in portfolio.values() if isinstance(p, dict))
        returns = np.array([fetch_yahoo_returns(symbol) for symbol in symbols]).T
        if returns.shape[0] < 2:
            return True
        volatility = np.std(returns, axis=0)
        if np.any(volatility > float(os.getenv('BLACK_SWAN_VOL_THRESHOLD', 0.5))):
            return False
        return portfolio_value > 2839 * float(os.getenv('SAFETY_BUFFER_THRESHOLD', 0.75))
    except Exception as e:
        print(f"Erreur stress test : {str(e)}")
        return True
