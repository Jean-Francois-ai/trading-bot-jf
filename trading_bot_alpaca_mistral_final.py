# trading_bot_alpaca_mistral_final.py
from openai import OpenAI
import requests
import time
import json
import re
import traceback
import datetime
import alpaca_trade_api as tradeapi
from alpha_vantage.timeseries import TimeSeries

# Configurations
ALPHA_VANTAGE_API_KEY = "343PVU511F4SHC8V"
OPENROUTER_API_KEY = "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"
ALPACA_API_KEY = "PKC594RRZABXG20W7HNC"
ALPACA_SECRET_KEY = "jn5BN0cEJHBe9I56lnNotH9iDXcGD1OqjNdFPCZK"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # URL explicite

class MarketData:
    def __init__(self, api_key):
        self.ts = TimeSeries(key=api_key, output_format='pandas')
    
    def get_real_time_data(self, symbol):
        try:
            data, _ = self.ts.get_quote_endpoint(symbol=symbol)
            latest_price = float(data.iloc[0]['05. price'])
            return {
                'symbol': symbol,
                'price': latest_price,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"❌ Erreur Alpha Vantage: {str(e)}")
            traceback.print_exc()
            return None

class TradingBotLLM:
    def __init__(self, api_key):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.model = "mistralai/mistral-7b-instruct:free"
    
    def generate_strategy(self, market_data):
        prompt = f"""
        [CONTEXTE MARCHÉ]
        Symbole: {market_data['symbol']} 
        Prix: ${market_data['price']}
        Heure: {market_data['timestamp']}
        
        [INSTRUCTIONS]
        En tant que quant expert, propose un iron condor SPY avec 3 jours jusqu'à expiration:
        1. Strikes spécifiques (call/put) - multiples de 5$
        2. Ratio risque/récompense
        3. Profit cible et stop-loss
        4. Quantité de contrats (max 5)
        
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
                timeout=30
            )
            
            json_str = response.choices[0].message.content.strip()
            if "```json" in json_str:
                json_str = re.search(r'```json(.*)```', json_str, re.DOTALL).group(1).strip()
            return json.loads(json_str)
        except Exception as e:
            print(f"❌ Erreur OpenRouter: {str(e)}")
            traceback.print_exc()
            return None

def convert_to_alpaca_option_symbol(symbol, strike, option_type, expiration_date):
    """Convertit vers le format option Alpaca (expiration YYMMDD)"""
    # Format spécifique Alpaca: SPY_YYMMDDC/Pstrike
    strike_str = f"{int(strike*1000):08d}"
    return f"{symbol}_{expiration_date}{'C' if option_type == 'call' else 'P'}{strike_str}"

def get_next_friday():
    """Calcule la date du prochain vendredi (format YYMMDD)"""
    today = datetime.date.today()
    days_ahead = (4 - today.weekday()) % 7
    if days_ahead <= 0:
        days_ahead += 7
    next_friday = today + datetime.timedelta(days=days_ahead)
    return next_friday.strftime("%y%m%d")

class AlpacaTrader:
    def __init__(self, api_key, secret_key):
        self.api = tradeapi.REST(
            api_key,
            secret_key,
            base_url=ALPACA_BASE_URL,
            api_version='v2'
        )
        try:
            account = self.api.get_account()
            print(f"\n🔑 Connecté à Alpaca Paper Trading")
            print(f"- Solde: ${account.cash}")
            print(f"- Options activées: {account.options_approved}")
        except Exception as e:
            print(f"❌ Erreur de connexion Alpaca: {str(e)}")
            traceback.print_exc()
    
    def execute_iron_condor(self, strategy):
        symbol = "SPY"
        qty = strategy['quantity']
        expiration = get_next_friday()
        
        # Ajustement des strikes aux multiples de 5
        strikes = {
            'call_short': 5 * round(strategy['call_short_strike'] / 5),
            'call_long': 5 * round(strategy['call_long_strike'] / 5),
            'put_short': 5 * round(strategy['put_short_strike'] / 5),
            'put_long': 5 * round(strategy['put_long_strike'] / 5)
        }
        
        print(f"\n⚙️ Configuration des options:")
        print(f"- Expiration: {expiration}")
        print(f"- Call short: {strikes['call_short']}")
        print(f"- Call long: {strikes['call_long']}")
        print(f"- Put short: {strikes['put_short']}")
        print(f"- Put long: {strikes['put_long']}")
        
        try:
            # Création des symboles
            call_short_symbol = convert_to_alpaca_option_symbol(symbol, strikes['call_short'], "call", expiration)
            call_long_symbol = convert_to_alpaca_option_symbol(symbol, strikes['call_long'], "call", expiration)
            put_short_symbol = convert_to_alpaca_option_symbol(symbol, strikes['put_short'], "put", expiration)
            put_long_symbol = convert_to_alpaca_option_symbol(symbol, strikes['put_long'], "put", expiration)
            
            print(f"\n🔧 Symboles d'options générés:")
            print(f"- Call short: {call_short_symbol}")
            print(f"- Call long: {call_long_symbol}")
            print(f"- Put short: {put_short_symbol}")
            print(f"- Put long: {put_long_symbol}")
            
            # Vérification de la disponibilité
            if not self._validate_option(call_short_symbol):
                return False
            
            # Exécution des ordres
            self._place_order(call_short_symbol, qty, "sell")
            self._place_order(call_long_symbol, qty, "buy")
            self._place_order(put_short_symbol, qty, "sell")
            self._place_order(put_long_symbol, qty, "buy")
            
            return True
        except Exception as e:
            print(f"❌ Erreur d'exécution Alpaca: {str(e)}")
            traceback.print_exc()
            return False
    
    def _validate_option(self, symbol):
        """Vérifie si une option est disponible"""
        try:
            asset = self.api.get_asset(symbol)
            if asset.tradable:
                return True
            print(f"❌ Option non tradable: {symbol}")
            return False
        except Exception as e:
            print(f"❌ Option non trouvée: {symbol} - {str(e)}")
            return False
    
    def _place_order(self, symbol, qty, side):
        """Place un ordre pour une option"""
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type="market",
                time_in_force="day",
                order_class="bracket",
                take_profit=dict(limit_price="1.0"),
                stop_loss=dict(stop_price="0.25", limit_price="0.24")
            )
            print(f"🔁 Ordre {side} exécuté: {qty} {symbol}")
            return order
        except Exception as e:
            print(f"❌ Échec de l'ordre {side} pour {symbol}: {str(e)}")
            raise

# --- Programme principal ---
if __name__ == "__main__":
    print("="*60)
    print("SYSTÈME DE TRADING AUTONOME ALPACA-MISTRAL (FINAL)")
    print("="*60)
    
    # Initialisation des services
    market_data = MarketData(ALPHA_VANTAGE_API_KEY)
    trading_bot = TradingBotLLM(OPENROUTER_API_KEY)
    trader = AlpacaTrader(ALPACA_API_KEY, ALPACA_SECRET_KEY)
    
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
                
                # Sauvegarde
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
