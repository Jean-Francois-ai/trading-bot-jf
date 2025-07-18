import numpy as np
from arch import arch_model
from utils.data_fetch import fetch_yahoo_returns
from dotenv import load_dotenv
import os
load_dotenv()

def garch_stop_loss(symbol):
    returns = fetch_yahoo_returns(f"{symbol}=X")
    model = arch_model(returns, vol='Garch', p=1, q=1)
    fit = model.fit(disp='off')
    vol = fit.conditional_volatility[-1]
    high_vol = float(os.getenv('GARCH_VOL_THRESHOLD_HIGH', 0.3))
    return 0.008 if vol > high_vol else 0.012

