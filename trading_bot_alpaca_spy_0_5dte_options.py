import requests
import datetime
import pytz
import time
import json  # Correction de l'importation

# Configuration Alpaca - REMPLACEZ PAR VOS CLÉS
ALPACA_API_KEY = "PKC594RRZABXG20W7HNC"
ALPACA_SECRET_KEY = "jn5BN0cEJHBe9I56lnNotH9iDXcGD1OqjNdFPCZK"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

def get_current_datetime():
    """Retourne la date/heure actuelle dans le fuseau horaire de trading"""
    return datetime.datetime.now(pytz.timezone('America/New_York'))

def get_dte_range():
    """Génère les dates d'expiration pour 0-5 DTE"""
    today = get_current_datetime().date()
    return [today + datetime.timedelta(days=i) for i in range(0, 6)]

def fetch_options_for_date(expiration_date):
    """Récupère les options SPY pour une date d'expiration spécifique"""
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
    }
    
    params = {
        "underlying_symbol": "SPY",
        "expiration_date": expiration_date.strftime("%Y-%m-%d"),
        "status": "active"
    }
    
    try:
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/options/contracts",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json().get('contracts', [])
            
        # Gestion spécifique du code 422 (paramètres invalides)
        if response.status_code == 422:
            error_data = response.json()
            print(f"⚠️ Erreur 422 pour {expiration_date}: {error_data.get('message')}")
            return []
            
        print(f"❌ Erreur {response.status_code} pour {expiration_date}: {response.text}")
        return []
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erreur réseau pour {expiration_date}: {str(e)}")
        return []

def get_0_to_5_dte_options():
    """Récupère toutes les options SPY avec 0-5 DTE"""
    dte_dates = get_dte_range()
    print(f"🔍 Recherche options 0-5 DTE pour dates: {[d.strftime('%Y-%m-%d') for d in dte_dates]}")
    
    all_contracts = []
    for expiration_date in dte_dates:
        contracts = fetch_options_for_date(expiration_date)
        if contracts:
            all_contracts.extend(contracts)
            print(f"✅ {len(contracts)} contrats trouvés pour {expiration_date.strftime('%Y-%m-%d')}")
        else:
            print(f"⚠️ Aucun contrat pour {expiration_date.strftime('%Y-%m-%d')}")
        
        time.sleep(0.2)  # Respect des limites de rate-limiting
    
    return all_contracts

def filter_and_analyze_contracts(contracts):
    """Filtre et analyse les contrats d'options"""
    if not contracts:
        return None
    
    # Filtre par type d'option
    calls = [c for c in contracts if c['option_type'] == 'call']
    puts = [c for c in contracts if c['option_type'] == 'put']
    
    # Tri par expiration (croissant) puis par strike (croissant)
    calls.sort(key=lambda x: (x['expiration_date'], x['strike']))
    puts.sort(key=lambda x: (x['expiration_date'], x['strike']))
    
    # Sélection des contrats les plus proches de l'expiration
    top_calls = calls[:5] if calls else []
    top_puts = puts[:5] if puts else []
    
    return {
        'all_contracts': contracts,
        'calls': calls,
        'puts': puts,
        'top_calls': top_calls,
        'top_puts': top_puts
    }

def main():
    print("=" * 70)
    current_time = get_current_datetime().strftime('%Y-%m-%d %H:%M:%S %Z')
    print(f"SYSTÈME DE RÉCUPÉRATION D'OPTIONS SPY 0-5 DTE - {current_time}")
    print("=" * 70)
    
    # Vérification rapide du compte
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
    }
    try:
        account_response = requests.get(f"{ALPACA_BASE_URL}/v2/account", headers=headers, timeout=5)
        if account_response.status_code == 200:
            account = account_response.json()
            print(f"🔑 Connecté à Alpaca Paper Trading (Solde: ${account.get('cash', 'N/A')})")
            print(f"📊 Niveau options: {account.get('options_approved_level', 'N/A')}")
        else:
            print(f"⚠️ Attention: Échec de vérification du compte ({account_response.status_code})")
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification du compte: {str(e)}")
    
    start_time = time.time()
    contracts = get_0_to_5_dte_options()
    elapsed = time.time() - start_time
    
    if not contracts:
        print("\n❌ Aucun contrat trouvé pour la plage 0-5 DTE")
        print("Vérifiez les points suivants:")
        print("1. Les options SPY sont-elles actuellement négociées?")
        print("2. Votre compte a-t-il les permissions options activées?")
        print("3. Essayez une date spécifique avec la commande cURL:")
        sample_date = get_current_datetime().date().strftime("%Y-%m-%d")
        print(f'   curl -H "APCA-API-KEY-ID: YOUR_KEY" -H "APCA-API-SECRET-KEY: YOUR_SECRET" \\')
        print(f'        "{ALPACA_BASE_URL}/v2/options/contracts?underlying_symbol=SPY&expiration_date={sample_date}"')
        return
    
    analysis = filter_and_analyze_contracts(contracts)
    
    print(f"\n✅ {len(contracts)} contrats trouvés en {elapsed:.2f}s")
    print(f"- Calls: {len(analysis['calls'])}")
    print(f"- Puts: {len(analysis['puts'])}")
    
    # Affichage des contrats les plus proches
    if analysis['top_calls']:
        print("\n🔹 Top 5 Calls (proche expiration):")
        for c in analysis['top_calls']:
            print(f"  - {c['symbol']} | Strike: ${c['strike']} | Exp: {c['expiration_date']}")
    
    if analysis['top_puts']:
        print("\n🔸 Top 5 Puts (proche expiration):")
        for c in analysis['top_puts']:
            print(f"  - {c['symbol']} | Strike: ${c['strike']} | Exp: {c['expiration_date']}")
    
    # Sauvegarde des résultats
    timestamp = get_current_datetime().strftime("%Y%m%d_%H%M%S")
    filename = f"spy_0_5dte_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(analysis, f, indent=2)
    print(f"\n💾 Résultats sauvegardés dans {filename}")

if __name__ == "__main__":
    main()
