# alpaca_spy_options_functional.py
import requests
import datetime
import pytz
import json

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

def get_spy_options():
    """Récupère et affiche les options disponibles pour SPY"""
    expiration = get_next_friday()
    print(f"\n🔍 Recherche des options SPY expirant le {expiration}")
    
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
    }
    
    try:
        # Récupération des options calls
        params_calls = {
            "underlying_symbol": "SPY",
            "expiration": expiration,
            "type": "call",
            "status": "active",
            "limit": 1000
        }
        response_calls = requests.get(
            f"{ALPACA_BASE_URL}/v2/options/contracts",
            headers=headers,
            params=params_calls
        )
        
        if response_calls.status_code != 200:
            print(f"❌ Erreur calls: {response_calls.status_code} - {response_calls.text}")
            return None
        
        # Récupération des options puts
        params_puts = {
            "underlying_symbol": "SPY",
            "expiration": expiration,
            "type": "put",
            "status": "active",
            "limit": 1000
        }
        response_puts = requests.get(
            f"{ALPACA_BASE_URL}/v2/options/contracts",
            headers=headers,
            params=params_puts
        )
        
        if response_puts.status_code != 200:
            print(f"❌ Erreur puts: {response_puts.status_code} - {response_puts.text}")
            return None
        
        # Extraction des données
        calls = response_calls.json().get('contracts', [])
        puts = response_puts.json().get('contracts', [])
        
        # Extraction des strikes
        call_strikes = sorted({c['strike'] for c in calls})
        put_strikes = sorted({p['strike'] for p in puts})
        
        print(f"\n📊 Options disponibles:")
        print(f"- Calls: {len(call_strikes)} strikes")
        print(f"- Puts: {len(put_strikes)} strikes")
        
        # Affichage des strikes autour du prix courant
        print("\n🔹 Calls (top 10):")
        print(call_strikes[:5] + ["..."] + call_strikes[-5:])
        
        print("\n🔸 Puts (top 10):")
        print(put_strikes[:5] + ["..."] + put_strikes[-5:])
        
        return {
            'expiration': expiration,
            'calls': call_strikes,
            'puts': put_strikes
        }
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return None

def verify_account():
    """Vérifie la connexion au compte"""
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
    }
    
    try:
        response = requests.get(f"{ALPACA_BASE_URL}/v2/account", headers=headers)
        if response.status_code == 200:
            account = response.json()
            print(f"\n🔑 Connecté à Alpaca Paper Trading")
            print(f"- ID: {account['id']}")
            print(f"- Solde: ${account['cash']}")
            print(f"- Options activées: {account.get('options_approved_level', 'Inconnu')}")
            return True
        print(f"❌ Erreur compte: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {str(e)}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("SYSTÈME FONCTIONNEL DE GESTION DES OPTIONS SPY SUR ALPACA")
    print("="*60)
    
    # Vérification du compte
    if not verify_account():
        exit()
    
    # Récupération des options
    options = get_spy_options()
    
    if options:
        print("\n✅ Récupération réussie!")
        print(f"Expiration: {options['expiration']}")
        print(f"Strike min call: {min(options['calls'])}")
        print(f"Strike max call: {max(options['calls'])}")
        print(f"Strike min put: {min(options['puts'])}")
        print(f"Strike max put: {max(options['puts'])}")
        
        # Exemple de symbole d'option
        strike = 630.0
        option_type = "call"
        symbol = f"O:SPY{expiration.replace('-', '')[2:]}{option_type[0].upper()}{int(strike * 1000):08d}"
        print(f"\n🧪 Exemple de symbole pour {strike} {option_type}: {symbol}")
    else:
        print("\n❌ Échec de la récupération des options")


