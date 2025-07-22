import os
from dotenv import load_dotenv
import pandas as pd
from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime

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
    symbol_or_symbols="AAPL250725C00110000",
    timeframe=TimeFrame.Day,  # Barres journalières
    start=datetime(2025, 1, 1),
    end=datetime(2025, 7, 22)
)

# Récupérer et afficher les données
try:
    bars = client.get_option_bars(request)
    df_bars = bars.df
    if not df_bars.empty:
        print("Données historiques pour AAPL250725C00110000 :")
        print(df_bars)
        # Enregistrer en CSV pour analyse ultérieure
        df_bars.to_csv("aapl_option_historical.csv", index=True)
        print("Données enregistrées dans aapl_option_historical.csv")
    else:
        print("Aucune donnée historique trouvée pour les paramètres donnés.")
except Exception as e:
    print(f"Erreur lors de la récupération des données historiques : {e}")
