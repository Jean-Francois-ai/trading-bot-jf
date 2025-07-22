# trading_bot_realtime.py
from openai import OpenAI
import requests
import time
import json
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators

# Configurations
ALPHA_VANTAGE_API_KEY = "343PVU511F4SHC8V"
OPENROUTER_API_KEY = "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"

class MarketData:
    def __init__(self, api_key):
        self.ts = TimeSeries(key=api_key, output_format='pandas')
        self.ti = TechIndicators(key=api_key, output_format='pandas')
    
    def get_real_time_data(self, symbol):
        """Récupère les données marché en temps réel"""
        try:
            # Données de prix
            data, _ = self.ts.get_quote_endpoint(symbol=symbol)
            latest_price = float(data['05. price'][0])
            
            # Données techniques
            rsi, _ = self.ti.get_rsi(symbol=symbol, interval='15min', time_period=14)
            latest_rsi = rsi['RSI'].iloc[-1]
            
            # Volatilité implicite (approximation)
            hist_data, _ = self.ts.get_daily(symbol=symbol, outputsize='compact')
            volatility = hist_data['4. close'].pct_change().std() * (252**0.5) * 100
            
            return {
                'symbol': symbol,
                'price': latest_price,
                'rsi': round(latest_rsi, 2),
                'volatility': round(volatility, 2),
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"❌ Erreur Alpha Vantage: {str(e)}")
            return None

class TradingBotLLM:
    def __init__(self, api_key):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.model = "mistralai/mistral-small-3.1-24b-instruct:free"
    
    def generate_strategy(self, market_data, dte=3):
        """Génère une stratégie basée sur les données marché"""
        prompt = f"""
        [CONTEXTE MARCHÉ]
        Symbole: {market_data['symbol']} 
        Prix: ${market_data['price']}
        RSI(14): {market_data['rsi']}
        Volatilité annuelle: {market_data['volatility']}%
        Heure: {market_data['timestamp']}
        
        [INSTRUCTIONS]
        En tant que quant expert, propose un iron condor avec {dte} jours jusqu'à expiration:
        1. Strikes spécifiques (call/put) basés sur le prix actuel et la volatilité
        2. Ratio risque/récompense optimal
        3. Gestion des risques adaptée au RSI et à la volatilité
        4. Profit cible et stop-loss quantitatifs
        5. Technique de hedging pour le gamma risk
        
        [EXIGENCES]
        - Structure la réponse en points techniques concis
        - Inclure les calculs clés (delta, crédit net, etc.)
        - Ne PAS donner de conseil financier
        - Terminer par ###ANALYSE COMPLÈTE###
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=700,
                timeout=20
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Erreur OpenRouter: {str(e)}")
            return None

# --- Programme principal ---
if __name__ == "__main__":
    # Initialisation des services
    market_data = MarketData(ALPHA_VANTAGE_API_KEY)
    trading_bot = TradingBotLLM(OPENROUTER_API_KEY)
    
    print("="*60)
    print("SYSTÈME DE TRADING EN TEMPS RÉEL")
    print("="*60)
    
    # Récupération des données marché
    spy_data = market_data.get_real_time_data("SPY")
    
    if spy_data:
        print(f"\n📊 Données SPY en temps réel:")
        print(f"- Prix: ${spy_data['price']}")
        print(f"- RSI(14): {spy_data['rsi']}")
        print(f"- Volatilité: {spy_data['volatility']}%")
        print(f"- Dernière mise à jour: {spy_data['timestamp']}")
        
        # Génération de stratégie
        strategy = trading_bot.generate_strategy(spy_data)
        
        if strategy:
            print("\n🔧 Stratégie générée:")
            print(strategy)
            
            # Simulation d'exécution
            print("\n✅ Stratégie prête pour exécution")
        else:
            print("❌ Échec de génération de stratégie")
    else:
        print("❌ Impossible de récupérer les données marché")

