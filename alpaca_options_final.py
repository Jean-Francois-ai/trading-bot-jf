import requests
import datetime
import pytz
import time
import json
import yfinance as yf
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOptionContractsRequest
from alpaca.trading.enums import AssetStatus, OptionType

# Configuration des APIs - REMPLACEZ PAR VOS CLÉS
ALPACA_API_KEY = "PKC594RRZABXG20W7HNC"
ALPACA_SECRET_KEY = "jn5BN0cEJHBe9I56lnNotH9iDXcGD1OqjNdFPCZK"

# Configuration du fuseau horaire
NY_TZ = pytz.timezone('America/New_York')

class MarketCalendar:
    """Calendrier du marché avec détection des jours fériés"""
    def __init__(self):
        self.holidays = self.load_holidays(datetime.datetime.now().year)
        
    def load_holidays(self, year):
        """Charge les jours fériés pour une année donnée (source: CBOE)"""
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
        """Vérifie si c'est un jour de trading (weekends et jours fériés exclus)"""
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
        
        # Ajouter les vendredis suivants
        for i in range(1, count):
            next_date = next_friday + datetime.timedelta(weeks=i)
            expirations.append(next_date.strftime("%Y-%m-%d"))
        
        return expirations

class MarketDataFetcher:
    """Classe pour récupérer les données de marché"""
    def __init__(self):
        self.calendar = MarketCalendar()
        self.trading_client = TradingClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, paper=True)
    
    def is_market_open(self):
        """Détermine si les marchés sont ouverts actuellement (9h30-16h EST)"""
        if not self.calendar.is_trading_day():
            return False
        
        now = datetime.datetime.now(NY_TZ)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def fetch_alpaca_options(self, expiration_date):
        """
        Récupère les options SPY d'Alpaca pour une date d'expiration
        Documentation: https://alpaca.markets/docs/api-references/trading-api/options/options-contract/
        """
        try:
            # Configuration de la requête selon la documentation
            request = GetOptionContractsRequest(
                underlying_symbol="SPY",
                expiration_date=expiration_date,
                status=AssetStatus.ACTIVE
            )
            
            # Récupération paginée des contrats
            all_contracts = []
            contracts = self.trading_client.get_option_contracts(request)
            all_contracts.extend(contracts)
            
            # Gestion de la pagination
            while contracts.next_page_token:
                request.page_token = contracts.next_page_token
                contracts = self.trading_client.get_option_contracts(request)
                all_contracts.extend(contracts)
            
            return all_contracts
        except Exception as e:
            print(f"Erreur Alpaca (options): {str(e)}")
            return []
    
    def fetch_alpaca_stock_price(self):
        """Récupère le prix SPY via Alpaca (dernier trade)"""
        try:
            # Méthode recommandée par la documentation
            latest_trade = self.trading_client.get_latest_trade("SPY")
            return latest_trade.price
        except Exception as e:
            print(f"Erreur Alpaca (prix SPY): {str(e)}")
            return None
    
    def fetch_yfinance(self):
        """Récupère les données de Yahoo Finance avec gestion d'erreurs améliorée"""
        try:
            # Utilisation d'une méthode plus robuste
            data = yf.download("SPY", period="1d", progress=False, timeout=10)
            return data['Close'].iloc[-1] if not data.empty else None
        except Exception as e:
            print(f"Erreur Yahoo Finance: {str(e)}")
            return None

class OptionsAnalyzer:
    """Analyse les données d'options avec gestion robuste des attributs"""
    @staticmethod
    def analyze_options(contracts):
        """Analyse les contrats d'options"""
        if not contracts:
            return None
        
        # Conversion en DataFrame avec vérification des attributs
        data = []
        for c in contracts:
            contract_data = {
                'symbol': c.symbol,
                'strike': c.strike,
                'option_type': c.option_type.value if hasattr(c, 'option_type') else None,
                'expiration_date': c.expiration_date,
                'volume': getattr(c, 'volume', 0),
                'open_interest': getattr(c, 'open_interest', 0)
            }
            data.append(contract_data)
        
        df = pd.DataFrame(data)
        
        # Analyse de base
        report = {
            "total_contracts": len(df),
            "expirations": df['expiration_date'].value_counts().to_dict(),
            "min_strike": df['strike'].min(),
            "max_strike": df['strike'].max(),
        }
        
        # Ratio calls/puts (si les données sont disponibles)
        if 'option_type' in df:
            calls = df[df['option_type'] == 'call']
            puts = df[df['option_type'] == 'put']
            report["call_put_ratio"] = len(calls) / max(1, len(puts))
        
        # Volume moyen (si disponible)
        if 'volume' in df and not df['volume'].isnull().all():
            report["avg_volume"] = df['volume'].mean()
        
        return report
    
    @staticmethod
    def print_analysis(report):
        """Affiche l'analyse des options"""
        if not report:
            print("Aucune donnée d'option à analyser")
            return
        
        print("\n📊 ANALYSE DES OPTIONS SPY:")
        print(f"- Contrats totaux: {report['total_contracts']}")
        
        if 'call_put_ratio' in report:
            print(f"- Ratio Calls/Puts: {report['call_put_ratio']:.2f}")
        
        print(f"- Strike min: ${report['min_strike']:.2f}")
        print(f"- Strike max: ${report['max_strike']:.2f}")
        
        if 'avg_volume' in report:
            print(f"- Volume moyen: {report['avg_volume']:.0f}")
        
        print("\n📅 Répartition par expiration:")
        for date, count in report['expirations'].items():
            print(f"  - {date}: {count} contrats")

def main():
    print("=" * 70)
    print("SYSTÈME DE SURVEILLANCE DE MARCHÉ OPTIMISÉ")
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
    print(f"Dates d'expiration: {expirations}")
    
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
        report["options_analysis"] = options_analysis
    else:
        print("\n❌ Aucune donnée d'option disponible")
    
    # Sauvegarde du rapport
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"market_report_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Rapport sauvegardé dans {filename}")
    print("\n✅ Exécution terminée avec succès!")

if __name__ == "__main__":
    main()
