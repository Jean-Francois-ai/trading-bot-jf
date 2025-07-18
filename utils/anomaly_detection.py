from utils.data_fetch import fetch_alpha_vantage_intraday
from dotenv import load_dotenv
import numpy as np
load_dotenv()

def detect_anomaly(symbol):
    returns = fetch_alpha_vantage_intraday(symbol, '1min')
    z_score = (returns[-1] - np.mean(returns)) / np.std(returns)
    return abs(z_score) > float(os.getenv('BLACK_SWAN_VOL_THRESHOLD', 0.5))
