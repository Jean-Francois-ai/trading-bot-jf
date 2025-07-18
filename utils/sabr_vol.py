import numpy as np
from dotenv import load_dotenv
import os
load_dotenv()

def sabr_vol(spot, strike, time_to_expiry, risk_free_rate, alpha, beta, rho, nu):
    """
    Calcule la volatilité SABR pour les options.
    """
    alpha = float(os.getenv('SABR_ALPHA', alpha))
    beta = float(os.getenv('SABR_BETA', beta))
    rho = float(os.getenv('SABR_RHO', rho))
    nu = float(os.getenv('SABR_NU', nu))
    F = spot
    K = strike
    T = time_to_expiry
    if F == K:
        vol = alpha / (F ** (1 - beta))
    else:
        z = (nu / alpha) * ((F * K) ** ((1 - beta) / 2)) * np.log(F / K)
        x = np.log((np.sqrt(1 - 2 * rho * z + z**2) + z - rho) / (1 - rho))
        vol = (alpha * z / x) / ((F * K) ** ((1 - beta) / 2)) * (1 + ((1 - beta)**2 / 24) * (np.log(F / K))**2 + ((1 - beta)**4 / 1920) * (np.log(F / K))**4)
    return vol
