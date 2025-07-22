import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOptionContractsRequest
from alpaca.data.historical import StockHistoricalDataClient, OptionHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, OptionLatestQuoteRequest
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

# Initialiser les clients
stock_client = StockHistoricalDataClient(api_key=API_KEY, secret_key=API_SECRET)
option_client = OptionHistoricalDataClient(api_key=API_KEY, secret_key=API_SECRET)
trading_client = TradingClient(api_key=API_KEY, secret_key=API_SECRET, paper=True)

# Récupérer les contrats d'options SPY
def get_option_contracts():
    try:
        request = GetOptionContractsRequest(
            underlying_symbols=["SPY"],
            status="active",
            expiration_date_gte=datetime(2025, 7, 1),  # Élargir la période
            expiration_date_lte=datetime(2025, 7, 31),
            limit=100
        )
        options = trading_client.get_option_contracts(request)
        return options.option_contracts
    except Exception as e:
        print(f"Erreur lors de la récupération des contrats d'options : {e}")
        return []

# Estimer le crédit pour un Iron Condor
def estimate_iron_condor_credit(quotes, short_call_symbol, long_call_symbol, short_put_symbol, long_put_symbol):
    try:
        credit = (
            quotes[short_call_symbol].bid_price - quotes[long_call_symbol].ask_price +
            quotes[short_put_symbol].bid_price - quotes[long_put_symbol].ask_price
        )
        return max(credit, 0.01)  # Éviter les crédits négatifs
    except KeyError:
        return 0.12  # Valeur par défaut

# Simuler une stratégie Iron Condor
def simulate_iron_condor(df, short_call_strike, long_call_strike, short_put_strike, long_put_strike, credit_received):
    df['profit_loss'] = 0.0
    for index, row in df.iterrows():
        stock_price = row['close']
        # Calculer le profit/perte à l'expiration
        if stock_price < long_put_strike:
            loss = (long_put_strike - short_put_strike - credit_received) * 100
        elif stock_price < short_put_strike:
            loss = (short_put_strike - stock_price - credit_received) * 100
        elif stock_price <= short_call_strike:
            loss = credit_received * 100  # Profit maximum
        elif stock_price < long_call_strike:
            loss = (short_call_strike - stock_price - credit_received) * 100
        else:
            loss = (short_call_strike - long_call_strike - credit_received) * 100
        # Gestion des risques : limiter la perte à 50% du crédit
        if abs(loss) > credit_received * 100 * 0.5:
            loss = -credit_received * 100 * 0.5
        df.at[index, 'profit_loss'] = loss
    return df

# Récupérer les données historiques de SPY
try:
    request = StockBarsRequest(
        symbol_or_symbols="SPY",
        timeframe=TimeFrame.Day,
        start=datetime(2025, 6, 22),
        end=datetime(2025, 7, 22)
    )
    bars = stock_client.get_stock_bars(request)
    df_bars = bars.df
    if not df_bars.empty:
        # Réinitialiser l'index
        if isinstance(df_bars.index, pd.MultiIndex):
            df_bars = df_bars.reset_index()
            if 'timestamp' in df_bars.columns:
                df_bars.set_index('timestamp', inplace=True)
            else:
                print("La colonne 'timestamp' n'est pas présente. Utilisation de l'index par défaut.")

        print("Colonnes du DataFrame brut :", df_bars.columns.tolist())
        print("Données historiques pour SPY (22 juin 2025 - 22 juillet 2025) :")
        print(df_bars[['close', 'volume']])

        # Récupérer les contrats d'options
        option_contracts = get_option_contracts()
        if option_contracts:
            # Sélectionner des strikes pour l'Iron Condor
            avg_price = df_bars['close'].mean()
            short_call_strike = avg_price * 1.02
            long_call_strike = avg_price * 1.03
            short_put_strike = avg_price * 0.98
            long_put_strike = avg_price * 0.97

            # Trouver les contrats les plus proches
            calls = [c for c in option_contracts if c.type == "call"]
            puts = [c for c in option_contracts if c.type == "put"]
            short_call = min(calls, key=lambda x: abs(x.strike_price - short_call_strike), default=None)
            long_call = min(calls, key=lambda x: abs(x.strike_price - long_call_strike), default=None)
            short_put = min(puts, key=lambda x: abs(x.strike_price - short_put_strike), default=None)
            long_put = min(puts, key=lambda x: abs(x.strike_price - long_put_strike), default=None)

            if all([short_call, long_call, short_put, long_put]):
                # Récupérer les cotations
                symbols = [short_call.symbol, long_call.symbol, short_put.symbol, long_put.symbol]
                quote_request = OptionLatestQuoteRequest(symbol_or_symbols=symbols)
                quotes = option_client.get_option_latest_quote(quote_request)
                credit_received = estimate_iron_condor_credit(quotes, short_call.symbol, long_call.symbol, short_put.symbol, long_put.symbol)
                print(f"Crédit estimé pour l'Iron Condor : {credit_received:.2f} $")
            else:
                credit_received = 0.12  # Valeur par défaut
                print("Impossible de trouver des contrats pour tous les strikes. Utilisation du crédit par défaut (0.12 $).")
        else:
            credit_received = 0.12
            print("Aucun contrat d'option trouvé. Utilisation du crédit par défaut (0.12 $).")

        # Simuler l'Iron Condor
        df_bars = simulate_iron_condor(df_bars, short_call_strike, long_call_strike, short_put_strike, long_put_strike, credit_received)

        # Calculer les profits cumulés
        df_bars['cumulative_profit'] = df_bars['profit_loss'].cumsum()

        print("\nRésultats de la stratégie Iron Condor :")
        print(df_bars[['close', 'profit_loss', 'cumulative_profit']])
        df_bars.to_csv("spy_iron_condor_realistic.csv", index=True)
        print("Résultats enregistrés dans spy_iron_condor_realistic.csv")

        # Visualisation
        try:
            plt.figure(figsize=(12, 6))
            plt.plot(df_bars.index, df_bars['close'], label='SPY Close Price', color='blue')
            plt.plot(df_bars.index, df_bars['cumulative_profit'], label='Cumulative Profit', color='green')
            plt.axhline(y=0, color='black', linestyle='--')
            plt.title('Stratégie Iron Condor sur SPY (0-5 DTE, 22 juin 2025 - 22 juillet 2025)')
            plt.xlabel('Date')
            plt.ylabel('Price / Profit ($)')
            plt.legend()
            plt.grid()
            plt.show()

            # Graphique des profits quotidiens
            plt.figure(figsize=(12, 4))
            plt.bar(df_bars.index, df_bars['profit_loss'], color=['green' if x > 0 else 'red' for x in df_bars['profit_loss']])
            plt.title('Profits quotidiens de Iron Condor sur SPY')
            plt.xlabel('Date')
            plt.ylabel('Profit/Loss ($)')
            plt.grid()
            plt.show()
        except Exception as plot_error:
            print(f"Erreur lors de la génération du graphique : {plot_error}")
    else:
        print("Aucune donnée historique trouvée pour SPY.")
except Exception as e:
    print(f"Erreur lors de la récupération des données historiques : {e}")
