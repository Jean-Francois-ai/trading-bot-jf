# trading_bot_integration.py
from openai import OpenAI
import time

class TradingBotLLM:
    def __init__(self, api_key):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.model = "mistralai/mistral-small-3.1-24b-instruct:free"
    
    def get_strategy(self, underlying, price, dte):
        """Génère une stratégie d'options basée sur les paramètres du marché"""
        prompt = f"""
        Tu es un expert quantitatif en options. Pour {underlying} à ${price} avec {dte} jours jusqu'à expiration:
        1. Propose un iron condor avec strikes spécifiques
        2. Définis les paramètres de gestion de risque
        3. Donne les cibles profit/stop-loss
        Sois concis, technique et pragmatique. Ne donne pas de conseil financier.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=600,
                timeout=15
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Erreur API: {str(e)}")
            return None

    def execute_strategy(self, symbol, current_price):
        """Exécute le workflow complet"""
        print(f"\n📈 Analyse de {symbol} à ${current_price}")
        strategy = self.get_strategy(symbol, current_price, 3)  # 3 DTE
        
        if strategy:
            print("\n🔧 Stratégie générée:")
            print(strategy)
            
            # Ici vous ajouteriez le code pour exécuter réellement le trade
            # via votre broker API (TD Ameritrade, Interactive Brokers, etc.)
            print("\n✅ Stratégie prête pour exécution")
        else:
            print("❌ Échec de génération de stratégie")

# Configuration
API_KEY = "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"

# Exemple d'utilisation
if __name__ == "__main__":
    bot = TradingBotLLM(API_KEY)
    
    # Exécuter pour SPY
    bot.execute_strategy("SPY", 520.50)
    
    # Exécuter pour QQQ
    bot.execute_strategy("QQQ", 450.75)



