# trading_bot_alpaca.py
from openai import OpenAI
import requests
import time
import json
from alpha_vantage.timeseries import TimeSeries
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Configurations
ALPHA_VANTAGE_API_KEY = "343PVU511F4SHC8V"
OPENROUTER_API_KEY = "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"
ALPACA_API_KEY = "PKC594RRZABXG20W7HNC"  # Clé Paper Trading
ALPACA_SECRET_KEY = "jn5BN0cEJHBe9I56lnNotH9iDXcGD1OqjNdFPCZK"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets/v2"  # URL de test

class MarketData:
    def __init__(self, api_key):
        self.ts = TimeSeries(key=api_key, output_format='pandas')
    
    def get_real_time_data(self, symbol):
        try:
            data, _ = self.ts.get_quote_endpoint(symbol=symbol)
            latest_price = float(data['05. price'][0])
            return {
                'symbol': symbol,
                'price': latest_price,
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
    
    def generate_strategy(self, market_data):
        prompt = f"""
        [CONTEXTE MARCHÉ]
        Symbole: {market_data['symbol']} 
        Prix: ${market_data['price']}
        Heure: {market_data['timestamp']}
        
        [INSTRUCTIONS]
        En tant que quant expert, propose un iron condor SPY avec 3 jours jusqu'à expiration:
        1. Strikes spécifiques (call/put)
        2. Ratio risque/récompense
        3. Profit cible et stop-loss
        4. Quantité de contrats (max 10)
        
        [FORMAT DE SORTIE - JSON]
        {{
          "strategy": "iron_condor",
          "call_short_strike": float,
          "call_long_strike": float,
          "put_short_strike": float,
          "put_long_strike": float,
          "credit_received": float,
          "profit_target": float,
          "stop_loss": float,
          "quantity": int,
          "analysis": "string"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=700,
                response_format={"type": "json_object"},
                timeout=20
            )
            
            return json.loads(response.choices[0].message.content.strip())
        except Exception as e:
            print(f"❌ Erreur OpenRouter: {str(e)}")
            return None

class AlpacaTrader:
    def __init__(self, api_key, secret_key, base_url):
        self.client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=True,
            base_url=base_url
        )
    
    def execute_iron_condor(self, strategy):
        symbol = "SPY"  # SPY options sur Alpaca
        qty = strategy['quantity']
        
        try:
            # Vendre call spread
            self._place_order(
                symbol=f"{symbol}{strategy['call_short_strike']}C",
                qty=qty,
                side=OrderSide.SELL
            )
            self._place_order(
                symbol=f"{symbol}{strategy['call_long_strike']}C",
                qty=qty,
                side=OrderSide.BUY
            )
            
            # Vendre put spread
            self._place_order(
                symbol=f"{symbol}{strategy['put_short_strike']}P",
                qty=qty,
                side=OrderSide.SELL
            )
            self._place_order(
                symbol=f"{symbol}{strategy['put_long_strike']}P",
                qty=qty,
                side=OrderSide.BUY
            )
            
            return True
        except Exception as e:
            print(f"❌ Erreur d'exécution Alpaca: {str(e)}")
            return False
    
    def _place_order(self, symbol, qty, side):
        order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=side,
            time_in_force=TimeInForce.DAY
        )
        
        order = self.client.submit_order(order_data)
        print(f"🔁 Ordre exécuté: {side} {qty} {symbol}")
        return order

# --- Programme principal ---
if __name__ == "__main__":
    print("="*60)
    print("SYSTÈME DE TRADING AUTONOME AVEC ALPACA")
    print("="*60)
    
    # Initialisation des services
    market_data = MarketData(ALPHA_VANTAGE_API_KEY)
    trading_bot = TradingBotLLM(OPENROUTER_API_KEY)
    trader = AlpacaTrader(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)
    
    # Récupération des données marché
    spy_data = market_data.get_real_time_data("SPY")
    
    if spy_data:
        print(f"\n📊 Données SPY en temps réel:")
        print(f"- Prix: ${spy_data['price']}")
        print(f"- Dernière mise à jour: {spy_data['timestamp']}")
        
        # Génération de stratégie
        strategy = trading_bot.generate_strategy(spy_data)
        
        if strategy:
            print("\n🔧 Stratégie générée:")
            print(json.dumps(strategy, indent=2))
            
            # Exécution automatique
            print("\n🚀 Exécution de la stratégie sur Alpaca...")
            if trader.execute_iron_condor(strategy):
                print("\n✅ Stratégie exécutée avec succès!")
                
                # Sauvegarde de la transaction
                with open("trade_history.json", "a") as f:
                    f.write(json.dumps({
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "strategy": strategy,
                        "market_data": spy_data
                    }) + "\n")
            else:
                print("❌ Échec d'exécution")
        else:
            print("❌ Échec de génération de stratégie")
    else:
        print("❌ Impossible de récupérer les données marché")
