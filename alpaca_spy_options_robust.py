# alpaca_spy_options_robust.py
import alpaca_trade_api as tradeapi
import datetime
import pytz
import requests
import time

# Configuration Alpaca
ALPACA_API_KEY = "PKC594RRZABXG20W7HNC"
ALPACA_SECRET_KEY = "jn5BN0cEJHBe9I56lnNotH9iDXcGD1OqjNdFPCZK"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

def get_next_friday():
    """Calcule la date du prochain vendredi (format YYYY-MM-DD)"""
    today = datetime.datetime.now(pytz.timezone('America/New_York'))
    days_ahead = (4 - today.weekday()) % 7
    if days_ahead == 0:  # Si aujourd'hui est vendredi
        days_ahead = 7
    next_friday = today + datetime.timedelta(days=days_ahead)
    return next_friday.strftime("%Y-%m-%d")

def get_spy_options(api):
    """Récupère et affiche les options disponibles pour SPY"""
    expiration = get_next_friday()
    print(f"\n🔍 Recherche des options SPY expirant le {expiration}")
    
    try:
        # Méthode 1: Utilisation de list_options_contracts (si disponible)
        if hasattr(api, 'list_options_contracts'):
            params = {
                'underlying_symbol': "SPY",
                'expiration_date': expiration,
                'status': 'active'
            }
            
            # Récupération paginée
            contracts = []
            page_token = None
            while True:
                if page_token:
                    params['page_token'] = page_token
                
                response = api.list_options_contracts(**params)
                contracts.extend(response)
                
                if hasattr(response, 'next_page_token') and response.next_page_token:
                    page_token = response.next_page_token
                else:
                    break
            
            # Séparation calls/puts
            calls = [c for c in contracts if c.option_type == 'call']
            puts = [c for c in contracts if c.option_type == 'put']
        else:
            # Méthode 2: Appel direct à l'API REST
            headers = {
                "APCA-API-KEY-ID": ALPACA_API_KEY,
                "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
            }
            
            # Récupération des calls
            params = {
                "underlying_symbol": "SPY",
                "expiration_date": expiration,
                "option_type": "call",
                "status": "active",
                "limit": 1000
            }
            response = requests.get(
                f"{ALPACA_BASE_URL}/v2/options/contracts",
                headers=headers,
                params=params
            )
            if response.status_code != 200:
                raise Exception(f"Erreur API calls: {response.status_code} - {response.text}")
            calls = response.json().get('contracts', [])
            
            # Récupération des puts
            params["option_type"] = "put"
            response = requests.get(
                f"{ALPACA_BASE_URL}/v2/options/contracts",
                headers=headers,
                params=params
            )
            if response.status_code != 200:
                raise Exception(f"Erreur API puts: {response.status_code} - {response.text}")
            puts = response.json().get('contracts', [])
        
        # Extraction des strikes
        call_strikes = sorted({c.strike if hasattr(c, 'strike') else c['strike'] for c in calls})
        put_strikes = sorted({p.strike if hasattr(p, 'strike') else p['strike'] for p in puts})
        
        print(f"\n📊 Options disponibles:")
        print(f"- Calls: {len(call_strikes)} strikes")
        print(f"- Puts: {len(put_strikes)} strikes")
        
        # Affichage des strikes autour du prix courant
        print("\n🔹 Calls autour du prix courant:")
        print(call_strikes[-10:])
        
        print("\n🔸 Puts autour du prix courant:")
        print(put_strikes[:10])
        
        return {
            'expiration': expiration,
            'calls': call_strikes,
            'puts': put_strikes
        }
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        traceback.print_exc()
        return None

def get_option_symbol(underlying, strike, option_type, expiration_date):
    """Génère le symbole d'option correct pour Alpaca"""
    # Format: O:SPY250725C00630000
    # - O: préfixe pour les options
    # - SPY: symbole sous-jacent
    # - 250725: date d'expiration (YYMMDD)
    # - C/P: type d'option
    # - 00630000: strike formaté sur 8 chiffres
    
    # Conversion de la date
    exp_date = datetime.datetime.strptime(expiration_date, "%Y-%m-%d")
    exp_formatted = exp_date.strftime("%y%m%d")
    
    # Formatage du strike
    strike_formatted = f"{int(float(strike) * 1000):08d}"
    
    return f"O:{underlying}{exp_formatted}{'C' if option_type == 'call' else 'P'}{strike_formatted}"

def verify_option_symbol(api, symbol):
    """Vérifie si un symbole d'option est valide"""
    try:
        # Méthode 1: Utilisation de get_options_contract (si disponible)
        if hasattr(api, 'get_options_contract'):
            contract = api.get_options_contract(symbol)
            return contract.tradable
        
        # Méthode 2: Appel direct à l'API REST
        headers = {
            "APCA-API-KEY-ID": ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
        }
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/options/contracts/{symbol}",
            headers=headers
        )
        
        if response.status_code == 200:
            return True
        return False
    except:
        return False

def main():
    print("="*60)
    print("SYSTÈME ROBUSTE DE GESTION DES OPTIONS SPY SUR ALPACA")
    print("="*60)
    
    # Initialisation de l'API Alpaca
    api = tradeapi.REST(
        ALPACA_API_KEY,
        ALPACA_SECRET_KEY,
        base_url=ALPACA_BASE_URL,
        api_version='v2'
    )
    
    # Vérification de la connexion
    try:
        account = api.get_account()
        print(f"\n🔑 Connecté à Alpaca Paper Trading")
        print(f"- Solde: ${account.cash}")
        print(f"- Options activées: {getattr(account, 'options_approved_level', 'Inconnu')}")
    except Exception as e:
        print(f"❌ Erreur de connexion: {str(e)}")
        return
    
    # 1. Récupération des options disponibles
    start_time = time.time()
    options = get_spy_options(api)
    duration = time.time() - start_time
    
    if options:
        print(f"\n✅ Récupération réussie en {duration:.2f}s")
        print(f"- Expiration: {options['expiration']}")
        print(f"- Strikes calls: {len(options['calls'])}")
        print(f"- Strikes puts: {len(options['puts'])}")
        
        # 2. Test de génération de symbole
        test_strike = 630.0
        test_type = "call"
        symbol = get_option_symbol("SPY", test_strike, test_type, options['expiration'])
        
        print(f"\n🧪 Test de génération de symbole:")
        print(f"- Strike: {test_strike}")
        print(f"- Type: {test_type}")
        print(f"- Symbole généré: {symbol}")
        
        # 3. Vérification du symbole
        is_valid = verify_option_symbol(api, symbol)
        print(f"- Symbole valide: {'Oui' if is_valid else 'Non'}")
        
        if not is_valid:
            # Tentative de recherche du bon format
            print("\n🔍 Recherche du bon format...")
            for contract in api.list_options_contracts(
                underlying_symbol="SPY",
                expiration_date=options['expiration'],
                strike=test_strike,
                option_type=test_type,
                status='active',
                limit=1
            ):
                print(f"- Format correct: {contract.symbol}")
                break
    else:
        print("\n❌ Échec de la récupération des options")

if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception as e:
        print(f"❌ Erreur critique: {str(e)}")
        traceback.print_exc()
