import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime

# Fonction pour calculer le RSI
def calculate_rsi(data, periods=6):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Charger le fichier .env
load_dotenv()

# Charger les clés API
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")

# Vérifier les clés API
if not API_KEY or not API_SECRET:
    raise ValueError("Les clés API (ALPACA_API_KEY ou ALPACA_SECRET_KEY) ne sont pas définies dans le fichier .env")

# Initialiser le client
client = OptionHistoricalDataClient(api_key=API_KEY, secret_key=API_SECRET)

# Configurer la requête pour les données historiques
request = OptionBarsRequest(
    symbol_or_symbols="AAPL251219C00200000",  # Changer pour un contrat avec plus de données
    timeframe=TimeFrame.Day,
    start=datetime(2024, 1, 1),  # Période plus longue
    end=datetime(2025, 7, 22)
)

# Récupérer les données et appliquer des stratégies
try:
    bars = client.get_option_bars(request)
    df_bars = bars.df
    if not df_bars.empty:
        # Stratégie de moyenne mobile
        df_bars['ma_short'] = df_bars['close'].rolling(window=3).mean()  # Réduire à 3 jours
        df_bars['ma_long'] = df_bars['close'].rolling(window=5).mean()   # Réduire à 5 jours
        df_bars['ma_signal'] = 0
        df_bars.loc[df_bars['ma_short'] > df_bars['ma_long'], 'ma_signal'] = 1  # Achat
        df_bars.loc[df_bars['ma_short'] < df_bars['ma_long'], 'ma_signal'] = -1 # Vente

        # Stratégie RSI
        df_bars['rsi'] = calculate_rsi(df_bars, periods=6)
        df_bars['rsi_signal'] = 0
        df_bars.loc[df_bars['rsi'] < 30, 'rsi_signal'] = 1  # Achat
        df_bars.loc[df_bars['rsi'] > 70, 'rsi_signal'] = -1 # Vente

        # Simuler les performances
        df_bars['returns'] = df_bars['close'].pct_change()
        df_bars['ma_strategy_returns'] = df_bars['returns'] * df_bars['ma_signal'].shift(1)
        df_bars['ma_cumulative_returns'] = (1 + df_bars['ma_strategy_returns']).cumprod() - 1
        df_bars['rsi_strategy_returns'] = df_bars['returns'] * df_bars['rsi_signal'].shift(1)
        df_bars['rsi_cumulative_returns'] = (1 + df_bars['rsi_strategy_returns']).cumprod() - 1

        # Afficher les résultats
        print("Résultats des stratégies (moyenne mobile et RSI) :")
        print(df_bars[['close', 'ma_short', 'ma_long', 'ma_signal', 'ma_cumulative_returns', 'rsi', 'rsi_signal', 'rsi_cumulative_returns']])
        df_bars.to_csv("aapl_option_strategies.csv", index=True)
        print("Résultats enregistrés dans aapl_option_strategies.csv")

        # Visualisation
        plt.figure(figsize=(12, 6))
        plt.plot(df_bars.index, df_bars['close'], label='Close Price', color='blue')
        plt.plot(df_bars.index, df_bars['ma_short'], label='MA Short (3 days)', color='orange')
        plt.plot(df_bars.index, df_bars['ma_long'], label='MA Long (5 days)', color='green')
        plt.scatter(df_bars[df_bars['ma_signal'] == 1].index, df_bars[df_bars['ma_signal'] == 1]['close'], 
                    marker='^', color='green', label='Buy Signal', s=100)
        plt.scatter(df_bars[df_bars['ma_signal'] == -1].index, df_bars[df_bars['ma_signal'] == -1]['close'], 
                    marker='v', color='red', label='Sell Signal', s=100)
        plt.title('Stratégie de moyenne mobile pour AAPL251219C00200000')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.legend()
        plt.grid()
        plt.show()

        plt.figure(figsize=(12, 4))
        plt.plot(df_bars.index, df_bars['rsi'], label='RSI (6 days)', color='purple')
        plt.axhline(70, color='red', linestyle='--', label='Overbought (70)')
        plt.axhline(30, color='green', linestyle='--', label='Oversold (30)')
        plt.title('RSI pour AAPL251219C00200000')
        plt.xlabel('Date')
        plt.ylabel('RSI')
        plt.legend()
        plt.grid()
        plt.show()
    else:
        print("Aucune donnée historique trouvée pour les paramètres donnés.")
except Exception as e:
    print(f"Erreur lors de la récupération des données historiques : {e}")
