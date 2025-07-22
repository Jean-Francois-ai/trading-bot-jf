# trading_bot_alpaca_mistral_fixed.py
from openai import OpenAI
import requests
import time
import json
import re
import traceback
import datetime
from alpha_vantage.timeseries import TimeSeries
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# Configurations
ALPHA_VANTAGE_API_KEY = "343PVU511F4SHC8V"
OPENROUTER_API_KEY = "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"
ALPACA_API_KEY = "PKC594RRZABXG20W7HNC"  # Clé Paper Trading
ALPACA_SECRET_KEY = "jn5BN0cEJHBe9I56lnNotH9iDXcGD1OqjNdFPCZK"

class MarketData:
    def __init__(self, api_key):
        self.ts = TimeSeries(key=api_key, output_format='pandas')
    
    def get_real_time_data(self, symbol):
        try:
            data, _ = self.ts.get_quote_endpoint(symbol=symbol)
            # Correction de l'accès aux données
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
        # Modèle gratuit garanti
        self.model = "mistralai/mistral-7b-instruct:free"
    
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
            
            # Gestion robuste de la réponse JSON
            json_str = response.choices[0].message.content.strip()
            if "```json" in json_str:
                json_str = re.search(r'```json(.*)```', json_str, re.DOTALL).group(1).strip()
            return json.loads(json_str)
        except Exception as e:
            print(f"❌ Erreur OpenRouter: {str(e)}")
            traceback.print_exc()
            return None

def convert_to_alpaca_option_symbol(symbol, strike, option_type, expiration_date):
    """Convertit vers le format option Alpaca (expiration YYYY-MM-DD)"""
    # Formatage du strike avec 5 zéros non significatifs (8 chiffres au total)
    strike_str = f"{int(strike*1000):08d}"
    return f"{symbol}_{expiration_date.replace('-', '')}{'C' if option_type == 'call' else 'P'}{strike_str}"

def get_next_friday():
    """Calcule la date du prochain vendredi (jour d'expiration des options)"""
    today = datetime.date.today()
    days_ahead = (4 - today.weekday()) % 7  # 0=Monday, 1=Tuesday, ..., 4=Vendredi
    if days_ahead <= 0:  # Si aujourd'hui est vendredi ou après
        days_ahead += 7
    next_friday = today + datetime.timedelta(days=days_ahead)
    return next_friday.strftime("%y%m%d")  # Format YYMMDD

class AlpacaTrader:
    def __init__(self, api_key, secret_key):
        self.client = TradingClient(
            api_key=api_key,
            secret_key=secret_key,
            paper=True  # Mode papier activé
        )
        # Vérification de la connexion
        try:
            account = self.client.get_account()
            print(f"\n🔑 Connecté à Alpaca ({'Paper' if account.trading_blocked else 'Live'} Trading)")
            print(f"- Solde: ${account.cash}")
            print(f"- Options activées: {'Oui' if account.options_approved else 'Non'}")
        except Exception as e:
            print(f"❌ Erreur de connexion Alpaca: {str(e)}")
            traceback.print_exc()
    
    def execute_iron_condor(self, strategy):
        symbol = "SPY"
        qty = strategy['quantity']
        expiration = get_next_friday()  # Date du prochain vendredi
        
        print(f"\n⚙️ Configuration des options:")
        print(f"- Expiration: {expiration}")
        print(f"- Call short: {strategy['call_short_strike']}")
        print(f"- Call long: {strategy['call_long_strike']}")
        print(f"- Put short: {strategy['put_short_strike']}")
        print(f"- Put long: {strategy['put_long_strike']}")
        
        try:
            # Création des symboles d'options
            call_short_symbol = convert_to_alpaca_option_symbol(symbol, strategy['call_short_strike'], "call", expiration)
            call_long_symbol = convert_to_alpaca_option_symbol(symbol, strategy['call_long_strike'], "call", expiration)
            put_short_symbol = convert_to_alpaca_option_symbol(symbol, strategy['put_short_strike'], "put", expiration)
            put_long_symbol = convert_to_alpaca_option_symbol(symbol, strategy['put_long_strike'], "put", expiration)
            
            print(f"\n🔧 Symboles d'options générés:")
            print(f"- Call short: {call_short_symbol}")
            print(f"- Call long: {call_long_symbol}")
            print(f"- Put short: {put_short_symbol}")
            print(f"- Put long: {put_long_symbol}")
            
            # Vérification préalable des symboles
            if not self._validate_symbol(call_short_symbol):
                return False
            
            # Vendre call spread
            self._place_order(
                symbol=call_short_symbol,
                qty=qty,
                side=OrderSide.SELL
            )
            self._place_order(
                symbol=call_long_symbol,
                qty=qty,
                side=OrderSide.BUY
            )
            
            # Vendre put spread
            self._place_order(
                symbol=put_short_symbol,
                qty=qty,
                side=OrderSide.SELL
            )
            self._place_order(
                symbol=put_long_symbol,
                qty=qty,
                side=OrderSide.BUY
            )
            
            return True
        except Exception as e:
            print(f"❌ Erreur d'exécution Alpaca: {str(e)}")
            traceback.print_exc()
            return False
    
    def _validate_symbol(self, symbol):
        """Vérifie si un symbole est valide"""
        try:
            asset = self.client.get_asset(symbol)
            if asset.tradable:
                return True
            print(f"❌ Symbole non tradable: {symbol}")
            return False
        except Exception as e:
            print(f"❌ Symbole invalide: {symbol} - {str(e)}")
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
    print("SYSTÈME DE TRADING AUTONOME ALPACA-MISTRAL (CORRIGÉ)")
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
