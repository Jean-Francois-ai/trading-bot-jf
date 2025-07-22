import requests
import datetime
import pytz
import json
import time

# Configuration Alpaca - Remplacez par vos clés
ALPACA_API_KEY = "PKC594RRZABXG20W7HNC"
ALPACA_SECRET_KEY = "jn5BN0cEJHBe9I56lnNotH9iDXcGD1OqjNdFPCZK"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

def get_third_friday(year, month):
    """Calcule le troisième vendredi du mois (format YYYY-MM-DD)"""
    first_day = datetime.datetime(year, month, 1)
    # Trouver le premier vendredi
    first_friday = first_day + datetime.timedelta(days=(4 - first_day.weekday()) % 7)
    # Troisième vendredi = premier vendredi + 14 jours
    third_friday = first_friday + datetime.timedelta(days=14)
    return third_friday.strftime("%Y-%m-%d")

def get_spy_options():
    """Récupère les options SPY avec expiration standard"""
    now = datetime.datetime.now(pytz.timezone('America/New_York'))
    expiration = get_third_friday(now.year, now.month)
    
    print(f"\n🔍 Recherche options SPY expirant le {expiration} (troisième vendredi)")
    
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
    }
    
    try:
        # Un seul appel API pour récupérer tous les contrats
        params = {
            "underlying_symbol": "SPY",
            "expiration_date": expiration,
            "status": "active"
        }
        
        start_time = time.time()
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/options/contracts",
            headers=headers,
            params=params
        )
        elapsed = time.time() - start_time
        
        print(f"⌛ Temps réponse: {elapsed:.2f}s | Statut: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Erreur API: {response.status_code}")
            print(f"URL: {response.url}")
            print(f"Réponse: {response.text}")
            return None
        
        contracts = response.json().get('contracts', [])
        
        if not contracts:
            print("⚠️ Aucun contrat trouvé. Vérifiez la date d'expiration.")
            return None
            
        # Séparation calls/puts
        calls = [c for c in contracts if c['option_type'] == 'call']
        puts = [c for c in contracts if c['option_type'] == 'put']
        
        # Extraction des strikes
        call_strikes = sorted({c['strike'] for c in calls})
        put_strikes = sorted({p['strike'] for p in puts})
        
        print(f"\n📊 Options trouvées: {len(contracts)} contrats")
        print(f"- Calls: {len(calls)} contrats | {len(call_strikes)} strikes")
        print(f"- Puts: {len(puts)} contrats | {len(put_strikes)} strikes")
        
        # Affichage des strikes autour de la monnaie
        print("\n🔹 Calls (strikes clés):")
        if call_strikes:
            mid = len(call_strikes) // 2
            print(call_strikes[mid-3:mid+3])
        
        print("\n🔸 Puts (strikes clés):")
        if put_strikes:
            mid = len(put_strikes) // 2
            print(put_strikes[mid-3:mid+3])
        
        return {
            'expiration': expiration,
            'calls': call_strikes,
            'puts': put_strikes
        }
        
    except Exception as e:
        print(f"❌ Erreur critique: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def verify_account():
    """Vérifie la connexion au compte et les permissions options"""
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
            
            # Vérification cruciale des permissions options
            options_level = account.get('options_approved_level', 'inconnu')
            print(f"- Niveau options: {options_level}")
            
            if options_level not in ['2', '3', 2, 3]:
                print("\n⚠️ ATTENTION: Votre compte n'a pas les permissions options nécessaires!")
                print("Activez le trading d'options dans le dashboard Alpaca")
                return False
                
            return True
            
        print(f"❌ Erreur compte: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion: {str(e)}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("SYSTÈME OPTIMISÉ DE RÉCUPÉRATION D'OPTIONS SPY")
    print("="*60)
    
    # Vérification du compte
    if not verify_account():
        print("\n❌ Arrêt du programme - Permissions insuffisantes")
        exit(1)
    
    # Tentative de récupération avec gestion des erreurs
    max_retries = 3
    options = None
    
    for attempt in range(max_retries):
        print(f"\n🚀 Tentative {attempt+1}/{max_retries}")
        options = get_spy_options()
        if options:
            break
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # Backoff exponentiel
            print(f"⏳ Nouvelle tentative dans {wait_time}s...")
            time.sleep(wait_time)
    
    if options:
        print("\n✅ Récupération réussie!")
        print(f"Expiration: {options['expiration']}")
        if options['calls']:
            print(f"Strike min call: ${min(options['calls'])}")
            print(f"Strike max call: ${max(options['calls'])}")
        if options['puts']:
            print(f"Strike min put: ${min(options['puts'])}")
            print(f"Strike max put: ${max(options['puts'])}")
        
        # Exemple de sélection d'une option
        if options['calls']:
            mid_index = len(options['calls']) // 2
            selected_call = options['calls'][mid_index]
            print(f"\n📈 Exemple d'option call ATM: SPY {options['expiration']} C ${selected_call}")
    else:
        print("\n❌ Échec de la récupération après plusieurs tentatives")
        print("Solutions possibles:")
        print("- Vérifiez vos clés API et l'URL")
        print("- Essayez avec une date d'expiration manuelle")
        print("- Contactez le support Alpaca si le problème persiste")
