# alpaca_spy_options.py
import alpaca_trade_api as tradeapi
import datetime
import pytz

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
        # Récupération des options calls
        calls = api.get_options_contracts(
            symbol="SPY",
            expiration=expiration,
            option_type="call",
            status="active"
        )
        
        # Récupération des options puts
        puts = api.get_options_contracts(
            symbol="SPY",
            expiration=expiration,
            option_type="put",
            status="active"
        )
        
        # Extraction des strikes
        call_strikes = sorted({c.strike for c in calls})
        put_strikes = sorted({p.strike for p in puts})
        
        print(f"\n📊 Options disponibles:")
        print(f"- Calls: {len(call_strikes)} strikes")
        print(f"- Puts: {len(put_strikes)} strikes")
        
        # Affichage des 10 premiers et derniers strikes
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

if __name__ == "__main__":
    print("="*60)
    print("RÉCUPÉRATION DES OPTIONS SPY SUR ALPACA")
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
        exit()
    
    # Récupération des options
    options = get_spy_options(api)
    
    if options:
        print("\n✅ Récupération réussie!")
        print(f"Strike minimum call: {min(options['calls'])}")
        print(f"Strike maximum call: {max(options['calls'])}")
        print(f"Strike minimum put: {min(options['puts'])}")
        print(f"Strike maximum put: {max(options['puts'])}")
