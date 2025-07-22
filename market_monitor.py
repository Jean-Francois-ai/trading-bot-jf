import requests
import datetime
import pytz
import time
import json
import yfinance as yf
from dateutil.relativedelta import relativedelta
import pandas as pd

# Configuration des APIs (À remplir avec vos clés)
ALPACA_API_KEY = "PKC594RRZABXG20W7HNC"
ALPACA_SECRET_KEY = "jn5BN0cEJHBe9I56lnNotH9iDXcGD1OqjNdFPCZK"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
ALPHA_VANTAGE_API_KEY = "343PVU511F4SHC8V"  # Optionnel

# Configuration du fuseau horaire
NY_TZ = pytz.timezone('America/New_York')

class MarketCalendar:
    """Calendrier du marché avec détection des jours fériés et jours ouvrés"""
    def __init__(self):
        self.holidays = self.load_holidays(datetime.datetime.now().year)
        
    def load_holidays(self, year):
        """Charge les jours fériés pour une année donnée"""
        # Source: CBOE (Chicago Board Options Exchange)
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
        if date.weekday() >= 5:  # Samedi(5) ou Dimanche(6)
            return False
        
        # Vérifier les jours fériés
        if date_str in self.holidays.values():
            return False
        
        return True
    
    def get_next_trading_days(self, days=5):
        """Retourne les prochains jours de trading"""
        now = datetime.datetime.now(NY_TZ)
        trading_days = []
        days_ahead = 0
        
        while len(trading_days) < days:
            candidate = now + datetime.timedelta(days=days_ahead)
            if self.is_trading_day(candidate):
                trading_days.append(candidate.date())
            days_ahead += 1
        
        return trading_days

class MarketDataFetcher:
    """Classe pour récupérer les données de marché de différentes sources"""
    def __init__(self):
        self.calendar = MarketCalendar()
    
    def is_market_open(self):
        """Détermine si les marchés sont ouverts actuellement"""
        if not self.calendar.is_trading_day():
            return False
        
        now = datetime.datetime.now(NY_TZ)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now <= market_close
    
    def fetch_alpaca_options(self, expiration_date):
        """Récupère les options SPY d'Alpaca pour une date d'expiration"""
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
            else:
                print(f"Erreur Alpaca ({response.status_code}): {response.text}")
                return []
                
        except Exception as e:
            print(f"Erreur réseau Alpaca: {str(e)}")
            return []
    
    def fetch_alpha_vantage(self):
        """Récupère les données d'Alpha Vantage"""
        try:
            # Utilisation de l'API plutôt que le package pour plus de flexibilité
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=SPY&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'Global Quote' in data:
                return float(data['Global Quote']['05. price'])
            return None
        except Exception as e:
            print(f"Erreur Alpha Vantage: {str(e)}")
            return None
    
    def fetch_yfinance(self):
        """Récupère les données de Yahoo Finance"""
        try:
            spy = yf.Ticker("SPY")
            data = spy.history(period="1d")
            return data['Close'].iloc[-1] if not data.empty else None
        except Exception as e:
            print(f"Erreur Yahoo Finance: {str(e)}")
            return None
    
    def compare_market_data(self):
        """Compare les données de différentes sources"""
        print("\n🔍 Comparaison des sources de données:")
        
        # Récupération des données
        alpaca_data = None
        alpha_data = self.fetch_alpha_vantage()
        yfinance_data = self.fetch_yfinance()
        
        # Si le marché est ouvert, essayer de récupérer les données temps réel d'Alpaca
        if self.is_market_open():
            try:
                # Exemple: récupérer le dernier prix SPY d'Alpaca
                headers = {
                    "APCA-API-KEY-ID": ALPACA_API_KEY,
                    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
                }
                response = requests.get(
                    f"{ALPACA_BASE_URL}/v2/stocks/SPY/trades/latest",
                    headers=headers,
                    timeout=5
                )
                if response.status_code == 200:
                    alpaca_data = response.json().get('trade', {}).get('p')
            except:
                pass
        
        # Préparation des résultats
        results = {}
        if alpaca_data: 
            results['alpaca'] = alpaca_data
            print(f"- Alpaca (temps réel): ${alpaca_data:.2f}")
        if alpha_data: 
            results['alpha_vantage'] = alpha_data
            print(f"- Alpha Vantage: ${alpha_data:.2f}")
        if yfinance_data: 
            results['yfinance'] = yfinance_data
            print(f"- Yahoo Finance: ${yfinance_data:.2f}")
        
        # Calcul des différences si plusieurs sources disponibles
        if len(results) > 1:
            prices = list(results.values())
            avg_price = sum(prices) / len(prices)
            
            comparisons = {}
            for source, price in results.items():
                diff = price - avg_price
                diff_pct = (diff / avg_price) * 100
                comparisons[source] = {
                    'price': price,
                    'diff_vs_avg': diff,
                    'diff_pct_vs_avg': diff_pct
                }
            
            print("\n📊 Écarts par rapport à la moyenne:")
            for source, data in comparisons.items():
                print(f"- {source}: {data['diff_pct_vs_avg']:+.4f}%")
            
            results['comparisons'] = comparisons
        
        return results

class OptionsAnalyzer:
    """Analyse les données d'options"""
    @staticmethod
    def analyze_options(contracts):
        """Analyse les contrats d'options"""
        if not contracts:
            return None
        
        # Conversion en DataFrame pour l'analyse
        df = pd.DataFrame(contracts)
        
        # Analyse de base
        report = {
            "total_contracts": len(df),
            "call_put_ratio": len(df[df['option_type'] == 'call']) / len(df[df['option_type'] == 'put']),
            "expirations": df['expiration_date'].value_counts().to_dict(),
            "min_strike": df['strike'].min(),
            "max_strike": df['strike'].max(),
            "avg_volume": df['volume'].mean() if 'volume' in df else None,
            "avg_oi": df['open_interest'].mean() if 'open_interest' in df else None
        }
        
        # Options les plus actives
        if 'volume' in df:
            report['top_calls'] = df[df['option_type'] == 'call'].nlargest(5, 'volume').to_dict('records')
            report['top_puts'] = df[df['option_type'] == 'put'].nlargest(5, 'volume').to_dict('records')
        
        return report
    
    @staticmethod
    def print_analysis(report):
        """Affiche l'analyse des options"""
        if not report:
            print("Aucune donnée à analyser")
            return
        
        print("\n📊 ANALYSE DES OPTIONS SPY:")
        print(f"- Contrats totaux: {report['total_contracts']}")
        print(f"- Ratio Calls/Puts: {report['call_put_ratio']:.2f}")
        print(f"- Strike min: ${report['min_strike']:.2f}")
        print(f"- Strike max: ${report['max_strike']:.2f}")
        
        if report.get('avg_volume'):
            print(f"- Volume moyen: {report['avg_volume']:.0f}")
        
        print("\n📅 Répartition par expiration:")
        for date, count in report['expirations'].items():
            print(f"  - {date}: {count} contrats")
        
        if 'top_calls' in report:
            print("\n🔝 TOP 5 CALLS (volume):")
            for call in report['top_calls']:
                print(f"  - {call['symbol']} | Strike: ${call['strike']} | Vol: {call['volume']}")

def main():
    print("=" * 70)
    print("SYSTÈME UNIVERSEL DE SURVEILLANCE DES MARCHÉS")
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
    
    # Récupération des données selon l'état du marché
    if market_open:
        print("\n🔍 Récupération des données options via Alpaca...")
        
        # Récupérer les prochains jours de trading
        trading_days = calendar.get_next_trading_days(5)
        print(f"Jours de trading: {[d.strftime('%Y-%m-%d') for d in trading_days]}")
        
        all_contracts = []
        for day in trading_days:
            contracts = fetcher.fetch_alpaca_options(day)
            if contracts:
                all_contracts.extend(contracts)
                print(f"✅ {len(contracts)} contrats trouvés pour {day}")
            else:
                print(f"⚠️ Aucun contrat trouvé pour {day}")
            time.sleep(0.5)  # Respect des limites de requêtes
        
        if all_contracts:
            # Analyse des options
            options_analysis = analyzer.analyze_options(all_contracts)
            analyzer.print_analysis(options_analysis)
            report["options_data"] = all_contracts
            report["options_analysis"] = options_analysis
    
    # Comparaison des données de marché
    market_comparison = fetcher.compare_market_data()
    if market_comparison:
        report["market_comparison"] = market_comparison
    
    # Sauvegarde du rapport
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"market_report_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Rapport sauvegardé dans {filename}")
    print("\n✅ Exécution terminée avec succès!")

if __name__ == "__main__":
    main()
