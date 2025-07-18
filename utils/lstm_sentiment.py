from dotenv import load_dotenv
import numpy as np
import os
load_dotenv()

def lstm_sentiment_prediction(sentiment_data):
    """
    Simule une prédiction de sentiment avec LSTM (version simplifiée pour paper trading).
    """
    score = sentiment_data.get('score', 0)
    return score if abs(score) <= float(os.getenv('SENTIMENT_SCORE_FILTER', -0.5)) else float(os.getenv('SENTIMENT_CRITICAL_THRESHOLD', -0.9))
