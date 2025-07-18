from utils.data_fetch import fetch_yahoo_returns
from dotenv import load_dotenv
import numpy as np
import os
load_dotenv()

def bayesian_quant(symbol, portfolio):
    """
    Estime la probabilité de profit avec une approche bayésienne simplifiée.
    """
    returns = fetch_yahoo_returns(f"{symbol}=X")
    mean_return = np.mean(returns)
    std_return = np.std(returns)
    prob_profit = 1 / (1 + np.exp(-(mean_return / std_return)))
    min_prob = float(os.getenv('MIN_PROB_PROFIT', 0.7))
    return prob_profit if prob_profit >= min_prob else 0.0
