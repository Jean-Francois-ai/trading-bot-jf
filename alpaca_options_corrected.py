import requests
import datetime
import pytz
import time
import json
import yfinance as yf
import pandas as pd
from alpaca.data.historical import OptionHistoricalDataClient
from alpaca.data.requests import OptionChainRequest
from alpaca.trading.client import TradingClient

# Configuration des APIs
ALPACA_API_KEY = "PKC594RRZABXG20W7HNC"
ALPACA_SECRET_KEY = "jn5BN0cEJHBe9I56lnNotH9iDXcGD1OqjNdFPCZK"
ALPHA_VANTAGE_API_KEY = "343PVU511F4SHC8V"  # Optionnel

# Configuration du fuseau horaire
NY_TZ = pytz.timezone('America/New_York')

class MarketCalendar:
    """Calendrier du marché avec détection des jours fériés"""
    def __init__(self):
        self.holidays = self.load_holidays(datetime.datetime.now().year)
        
    def load_holidays(self, year):
        """Charge les jours fériés pour une année donnée"""
        return {
            "New Year's Day": f"{year}-01-01",
            "Martin Luther King Jr. Day": f"{year}-01-20",
            "Washington's Birthday": f"{year}-02-17",
            "Good Friday": f"{year}-04-18",
            "Memorial Day": f"{year}-05-26",
            "Juneteenth": f"{year}-06-19",
            "Independence Day": f"{year}-07-04",
            "Labor Day": f"{year}-09-01",
            "Thanksgiving": f"{year}-11-27",
            "Christmas": f"{year}-12-25"
        }
    
    def is_trading_day(self, date=None):
        """Vérifie si c'est un jour de trading"""
        date = date or datetime.datetime.now(NY_TZ)
        date_str = date.strftime("%Y-%m-%d")
        
        # Vérifier les weekends
        if date.weekday() >= 5:
            return False
        
        # Vérifier les jours fériés
        if date_str in self.holidays.values():
            return False
        
        return True
    
    def get_next_expirations(self, count=4):
        """Retourne les prochaines dates d'expiration valides (vendredis)"""
        now = datetime.datetime.now(NY_TZ)
        expirations = []
        
        # Trouver le prochain vendredi
        days_ahead = (4 - now.weekday()) % 7
        if days_ahead == 0:  # Si aujourd'hui est vendredi
            days_ahead = 7
        
        next_friday = now + datetime.timedelta(days=days_ahead)
        expirations.append(next_friday.strftime("%Y-%m-%d"))
        
        # Ajouter 3 autres vendredis
        for i in range(1, count):
            next_date = next_friday + datetime.timedelta(weeks=i)
            expirations.append(next_date.strftime("%Y-%m-%d"))
        
        return expirations

class MarketDataFetcher:
    """Classe pour récupérer les données de marché"""
    def __init__(self):
        self.calendar = MarketCalendar()
        self.option_client = OptionHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
    
    def is_market_open(self):
        """Détermine si les marchés sont ouverts actuellement"""
        if not self.calendar.is_trading_day():
            return False
        
        now = datetime.datetime.now(NY_TZ)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def fetch_alpaca_options(self, expiration_date):
        """Récupère les options SPY d'Alpaca avec la nouvelle méthode"""
        try:
            # Utilisation de OptionChainRequest pour récupérer la chaîne d'options
            request = OptionChainRequest(
                underlying_symbol="SPY",
                expiration_date=expiration_date
            )
            
            # Récupère la chaîne d'options pour la date d'expiration
            option_chain = self.option_client.get_option_chain(request)
            
            # Convertir le dictionnaire en liste de contrats
            return list(option_chain.values())
        except Exception as e:
            print(f"Erreur lors de la récupération de la chaîne d'options pour {expiration_date}: {str(e)}")
            return []
    
    def fetch_alpaca_stock_price(self):
        """Récupère le prix de SPY via Alpaca"""
        try:
            # Utilisation du TradingClient pour les données temps réel
            trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
            latest_quote = trading_client.get_latest_quote("SPY")
            return latest_quote.ask_price
        except Exception as e:
            print(f"Erreur Alpaca (prix SPY): {str(e)}")
            return None
    
    def fetch_yfinance(self):
        """Récupère les données de Yahoo Finance"""
        try:
            # Utilisation d'une méthode plus robuste
            data = yf.download("SPY", period="1d", progress=False)
            return data['Close'].iloc[-1] if not data.empty else None
        except Exception as e:
            print(f"Erreur Yahoo Finance: {str(e)}")
            return None
    
    def compare_market_data(self):
        """Compare les données de différentes sources"""
        print("\n🔍 Comparaison des sources de données:")
        
        alpaca_price = self.fetch_alpaca_stock_price()
        yfinance_price = self.fetch_yfinance()
        
        results = {}
        if alpaca_price: 
            results['alpaca'] = alpaca_price
            print(f"- Alpaca: ${alpaca_price:.2f}")
        if yfinance_price: 
            results['yfinance'] = yfinance_price
            print(f"- Yahoo Finance: ${yfinance_price:.2f}")
        
        return results

class OptionsAnalyzer:
    """Analyse les données d'options"""
    @staticmethod
    def analyze_options(contracts):
        """Analyse les contrats d'options"""
        if not contracts:
            return None
        
        # Conversion en DataFrame pour l'analyse
        df = pd.DataFrame([{
            'symbol': c.symbol,
            'expiration': c.expiration.strftime("%Y-%m-%d"),  # Correction ici
            'strike': c.strike,
            'option_type': c.option_type.value,  # Enum -> str
            'volume': c.volume,
            'open_interest': c.open_interest
        } for c in contracts])
        
        # Analyse de base
        report = {
            "total_contracts": len(df),
            "call_put_ratio": len(df[df['option_type'] == 'call']) / max(1, len(df[df['option_type'] == 'put'])),
            "expirations": df['expiration'].value_counts().to_dict(),
            "min_strike": df['strike'].min(),
            "max_strike": df['strike'].max(),
            "avg_volume": df['volume'].mean() if 'volume' in df and not df['volume'].isnull().all() else None
        }
        
        return report
    
    @staticmethod
    def print_analysis(report):
        """Affiche l'analyse des options"""
        if not report:
            print("Aucune donnée d'option à analyser")
            return
        
        print("\n📊 ANALYSE DES OPTIONS SPY:")
        print(f"- Contrats totaux: {report['total_contracts']}")
        print(f"- Ratio Calls/Puts: {report['call_put_ratio']:.2f}")
        print(f"- Strike min: ${report['min_strike']:.2f}")
        print(f"- Strike max: ${report['max_strike']:.2f}")
        
        if report.get('avg_volume') is not None:
            print(f"- Volume moyen: {report['avg_volume']:.0f}")
        
        print("\n📅 Répartition par expiration:")
        for date, count in report['expirations'].items():
            print(f"  - {date}: {count} contrats")

def main():
    print("=" * 70)
    print("SYSTÈME MISE À JOUR AVEC CORRECTIONS API OPTIONS")
    print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Fuseau horaire: {NY_TZ.zone}")
    print("=" * 70)
    
    # Initialisation des composants
    fetcher = MarketDataFetcher()
    analyzer = OptionsAnalyzer()
    calendar = MarketCalendar()
    
    # Vérification de l'état du marché
    market_open = fetcher.is_market_open()
    market_status = "OUVERT" if market_open else "FERMÉ"
    print(f"\n📊 ÉTAT DU MARCHÉ: {market_status}")
    
    # Rapport final
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "market_status": market_status,
        "trading_day": calendar.is_trading_day()
    }
    
    # Récupération des options
    print("\n🔍 Récupération des données options...")
    expirations = calendar.get_next_expirations()
    print(f"Dates d'expiration recherchées: {expirations}")
    
    all_contracts = []
    for expiration in expirations:
        contracts = fetcher.fetch_alpaca_options(expiration)
        if contracts:
            all_contracts.extend(contracts)
            print(f"✅ {len(contracts)} contrats trouvés pour {expiration}")
        else:
            print(f"⚠️ Aucun contrat trouvé pour {expiration}")
        time.sleep(0.5)  # Respect des limites de requêtes
    
    # Analyse des options
    if all_contracts:
        options_analysis = analyzer.analyze_options(all_contracts)
        analyzer.print_analysis(options_analysis)
        report["options_data_count"] = len(all_contracts)
        report["options_analysis"] = options_analysis
    else:
        print("\n❌ Aucune donnée d'option disponible")
        # Solution de secours : afficher les derniers prix connus
        print("\n🔍 Récupération des derniers prix de SPY...")
        spy_data = fetcher.compare_market_data()
        if spy_data:
            report["spy_price"] = spy_data
    
    # Sauvegarde du rapport
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"market_report_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Rapport sauvegardé dans {filename}")
    print("\n✅ Exécution terminée avec succès!")

if __name__ == "__main__":
    main()
