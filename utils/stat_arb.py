import numpy as np
import logging

# Configurer le logging
logging.basicConfig(
    filename='stat_arb.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def stat_arb_opportunity(symbol, returns, option_chain):
    """Identifie les opportunités d’arbitrage statistique."""
    try:
        if not returns or len(returns) == 0:
            logger.warning(f"Aucune donnée de rendements pour {symbol}")
            return None

        # Calculer la moyenne et l’écart-type des rendements
        returns = np.array(returns, dtype=float)
        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # Stratégie simple : allouer si le dernier rendement est positif
        if len(returns) > 0 and returns[-1] > 0:
            alloc = {
                "asset": symbol,
                "alloc": min(0.1, max(0.01, mean_return / (std_return + 1e-6))),  # Allocation dynamique
                "position_type": "buy"
            }
            logger.info(f"Opportunité détectée pour {symbol} : {alloc}")
            return alloc
        else:
            logger.info(f"Aucune opportunité pour {symbol} : dernier rendement {returns[-1] if len(returns) > 0 else 'vide'}")
            return None
    except Exception as e:
        logger.error(f"Erreur stat_arb_opportunity pour {symbol} : {str(e)}")
        return None
