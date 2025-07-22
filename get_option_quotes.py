import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOptionContractsRequest
from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionLatestQuoteRequest
from datetime import datetime

# Charger le fichier .env
load_dotenv()

# Charger les clés API depuis les variables d'environnement
API_KEY = os.getenv("ALPACA_API_KEY")
API_SECRET = os.getenv("ALPACA_SECRET_KEY")

# Vérifier que les clés API sont définies
if not API_KEY or not API_SECRET:
    raise ValueError("Les clés API (ALPACA_API_KEY ou ALPACA_SECRET_KEY) ne sont pas définies dans le fichier .env")

# Initialiser les clients
trading_client = TradingClient(api_key=API_KEY, secret_key=API_SECRET, paper=True)
options_client = OptionHistoricalDataClient(api_key=API_KEY, secret_key=API_SECRET)

# Configurer la requête pour les contrats d'options
request_params = GetOptionContractsRequest(
    underlying_symbols=["AAPL"],  # Symbole sous-jacent
    status="active",              # Contrats actifs uniquement
    expiration_date_gte=datetime(2025, 7, 1),  # Date d'expiration après juillet 2025
    expiration_date_lte=datetime(2025, 12, 31),  # Date d'expiration avant décembre 2025
    type="call",                  # Type d'option (call ou put)
    limit=10000                   # Limite de 10 000 contrats par requête
)

# Récupérer les contrats d'options avec pagination
try:
    option_contracts = []
    options = trading_client.get_option_contracts(request_params)
    option_contracts.extend(options.option_contracts)

    # Gérer la pagination
    while options.next_page_token:
        request_params.page_token = options.next_page_token
        options = trading_client.get_option_contracts(request_params)
        option_contracts.extend(options.option_contracts)

    # Afficher les données brutes
    if option_contracts:
        print("Contrats d'options récupérés (données brutes) :")
        for contract in option_contracts[:5]:  # Limiter à 5 pour l'exemple
            print(contract.__dict__)

        # Récupérer les cotations en temps réel
        symbols = [contract.symbol for contract in option_contracts[:5]]  # Limiter à 5 pour éviter les limites de taux
        quote_request = OptionLatestQuoteRequest(symbol_or_symbols=symbols)
        quotes = options_client.get_option_latest_quote(quote_request)
        print("\nCitations en temps réel :")
        for symbol, quote in quotes.items():
            print(f"Symbole: {symbol}, Bid: {quote.bid_price}, Ask: {quote.ask_price}")
    else:
        print("Aucun contrat d'option trouvé pour les paramètres donnés.")
except Exception as e:
    print(f"Erreur lors de la récupération des contrats ou cotations : {e}")
