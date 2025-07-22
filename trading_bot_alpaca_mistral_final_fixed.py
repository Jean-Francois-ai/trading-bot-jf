# trading_bot_alpaca_mistral_final_fixed.py
from openai import OpenAI
import requests
import time
import json
import re
import traceback
import datetime
import alpaca_trade_api as tradeapi
from alpha_vantage.timeseries import TimeSeries
import pytz

# Configurations
ALPHA_VANTAGE_API_KEY = "343PVU511F4SHC8V"
OPENROUTER_API_KEY = "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"
ALPACA_API_KEY = "PKC594RRZABXG20W7HNC"
ALPACA_SECRET_KEY = "jn5BN0cEJHBe9I56lnNotH9iDXcGD1OqjNdFPCZK"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

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
    
    def generate_strategy(self, market_data, available_strikes):
        prompt = f"""
        [CONTEXTE MARCHÉ]
        Symbole: {market_data['symbol']} 
        Prix: ${market_data['price']}
        Heure: {market_data['timestamp']}
        Strikes disponibles: {available_strikes}
        
        [INSTRUCTIONS]
        En tant que quant expert, propose un iron condor SPY avec 3 jours jusqu'à expiration:
        1. Choisir les strikes parmi les options disponibles
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

class AlpacaTrader:
    def __init__(self, api_key, secret_key):
        self.api = tradeapi.REST(
            api_key,
            secret_key,
            base_url=ALPACA_BASE_URL,
            api_version='v2'
        )
        self.option_chain = {}
        try:
            account = self.api.get_account()
            print(f"\n🔑 Connecté à Alpaca Paper Trading")
            print(f"- Solde: ${account.cash}")
            
            if hasattr(account, 'options_approved'):
                print(f"- Options activées: {account.options_approved}")
            elif hasattr(account, 'options_approved_level'):
                print(f"- Niveau d'approbation options: {account.options_approved_level}")
            else:
                print("- Impossible de vérifier le statut des options")
        except Exception as e:
            print(f"❌ Erreur de connexion Alpaca: {str(e)}")
            traceback.print_exc()
    
    def get_available_options(self, symbol="SPY", days_to_exp=3):
        """Récupère les options disponibles pour un symbole donné"""
        try:
            # Calcul de la date d'expiration
            today = datetime.datetime.now(pytz.timezone('America/New_York'))
            expiration = today + datetime.timedelta(days=days_to_exp)
            
            # Trouver le vendredi suivant
            days_to_friday = (4 - today.weekday()) % 7
            if days_to_friday == 0:  # Si aujourd'hui est vendredi
                days_to_friday = 7
            expiration = today + datetime.timedelta(days=days_to_friday)
            expiration_str = expiration.strftime("%Y-%m-%d")
            
            # Récupération des options
            options = self.api.get_options_contracts(
                symbol,
                expiration=expiration_str,
                status='active'
            )
            
            # Organisation par type et strike
            chain = {'call': [], 'put': []}
            for option in options:
                if option.expiration == expiration_str:
                    chain[option.type].append(option.strike)
            
            # Tri et déduplication
            chain['call'] = sorted(set(chain['call']))
            chain['put'] = sorted(set(chain['put']))
            
            print(f"\n📊 Options disponibles pour {symbol} expirant le {expiration_str}:")
            print(f"- Calls: {len(chain['call'])} strikes")
            print(f"- Puts: {len(chain['put'])} strikes")
            
            self.option_chain = chain
            return chain
        except Exception as e:
            print(f"❌ Erreur de récupération des options: {str(e)}")
            traceback.print_exc()
            return {'call': [], 'put': []}
    
    def find_closest_strike(self, target, option_type):
        """Trouve le strike le plus proche disponible"""
        if not self.option_chain.get(option_type):
            return target
        
        return min(self.option_chain[option_type], key=lambda x: abs(x - target))
    
    def execute_iron_condor(self, strategy):
        symbol = "SPY"
        qty = strategy['quantity']
        
        # Récupérer les options disponibles
        if not self.option_chain:
            self.get_available_options(symbol)
        
        # Ajuster les strikes aux options disponibles
        adjusted_strategy = {
            'call_short': self.find_closest_strike(strategy['call_short_strike'], 'call'),
            'call_long': self.find_closest_strike(strategy['call_long_strike'], 'call'),
            'put_short': self.find_closest_strike(strategy['put_short_strike'], 'put'),
            'put_long': self.find_closest_strike(strategy['put_long_strike'], 'put'),
            'quantity': qty
        }
        
        print(f"\n⚙️ Configuration des options (après ajustement):")
        print(f"- Call short: {adjusted_strategy['call_short']}")
        print(f"- Call long: {adjusted_strategy['call_long']}")
        print(f"- Put short: {adjusted_strategy['put_short']}")
        print(f"- Put long: {adjusted_strategy['put_long']}")
        
        try:
            # Création des symboles avec les strikes ajustés
            call_short_symbol = self._get_option_symbol(symbol, adjusted_strategy['call_short'], 'call')
            call_long_symbol = self._get_option_symbol(symbol, adjusted_strategy['call_long'], 'call')
            put_short_symbol = self._get_option_symbol(symbol, adjusted_strategy['put_short'], 'put')
            put_long_symbol = self._get_option_symbol(symbol, adjusted_strategy['put_long'], 'put')
            
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
    
    def _get_option_symbol(self, symbol, strike, option_type):
        """Génère le symbole d'option correct pour Alpaca"""
        # Recherche dans la chaîne d'options
        for option in self.api.list_options_contracts({
            'underlying_symbol': symbol,
            'strike': strike,
            'type': option_type,
            'status': 'active'
        }):
            if option.strike == strike:
                return option.symbol
        
        # Fallback si non trouvé
        return f"{symbol}_{datetime.date.today().strftime('%y%m%d')}{'C' if option_type == 'call' else 'P'}{int(strike)}"
    
    def _place_order(self, symbol, qty, side):
        """Place un ordre pour une option"""
        try:
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type="market",
                time_in_force="day"
            )
            print(f"🔁 Ordre {side} exécuté: {qty} {symbol}")
            return order
        except Exception as e:
            print(f"❌ Échec de l'ordre {side} pour {symbol}: {str(e)}")
            raise

# --- Programme principal ---
if __name__ == "__main__":
    print("="*60)
    print("SYSTÈME DE TRADING AUTONOME ALPACA-MISTRAL (AVEC OPTIONS DISPONIBLES)")
    print("="*60)
    
    # Initialisation des services
    market_data = MarketData(ALPHA_VANTAGE_API_KEY)
    trader = AlpacaTrader(ALPACA_API_KEY, ALPACA_SECRET_KEY)
    
    # Récupération des données marché
    spy_data = market_data.get_real_time_data("SPY")
    
    if spy_data:
        print(f"\n📊 Données SPY en temps réel:")
        print(f"- Prix: ${spy_data['price']}")
        print(f"- Dernière mise à jour: {spy_data['timestamp']}")
        
        # Récupérer les options disponibles
        option_chain = trader.get_available_options("SPY")
        available_strikes = f"Calls: {option_chain['call'][:5]}... Puts: {option_chain['put'][:5]}..."
        
        # Initialisation du bot LLM avec les strikes disponibles
        trading_bot = TradingBotLLM(OPENROUTER_API_KEY)
        
        # Génération de stratégie avec les options disponibles
        strategy = trading_bot.generate_strategy(spy_data, available_strikes)
        
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
                        "market_data": spy_data,
                        "adjusted_strategy": trader.adjusted_strategy
                    }) + "\n")
            else:
                print("❌ Échec d'exécution")
        else:
            print("❌ Échec de génération de stratégie")
    else:
        print("❌ Impossible de récupérer les données marché")
