# trading_bot_reliable.py
from openai import OpenAI
import time
import requests

# Configuration OpenRouter
API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1"

# Test de connectivité
def test_connectivity():
    print("🔎 Test de connectivité vers OpenRouter...")
    try:
        response = requests.get("https://openrouter.ai", timeout=5)
        if response.status_code == 200:
            print("✅ Connectivité: HTTP 200")
            return True
        else:
            print(f"⚠️ Connectivité anormale: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Échec de connexion: {str(e)}")
        return False

# Test d'un modèle fiable
def test_model(model_name, prompt):
    print(f"\n🚀 Test du modèle: {model_name}")
    client = OpenAI(base_url=OPENROUTER_URL, api_key=API_KEY)
    
    try:
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
            timeout=20
        )
        
        elapsed_time = time.time() - start_time
        content = response.choices[0].message.content.strip()
        
        print(f"\n✅ Réponse reçue en {elapsed_time:.2f}s:")
        print(content)
        print("\n" + "-"*50)
        print(f"Tokens utilisés: {response.usage.total_tokens}")
        return True
            
    except Exception as e:
        print(f"\n❌ Erreur: {str(e)}")
        return False

# --- Programme principal ---
if __name__ == "__main__":
    print("="*60)
    print("STRATÉGIE TRADING - VERSION OPTIMISÉE")
    print("="*60)
    
    if not test_connectivity():
        exit(1)
    
    # Prompt optimisé
    test_prompt = (
        "Tu es un expert en options sur SPY. "
        "Décris brièvement comment mettre en place un iron condor avec 0-5 DTE. "
        "Points clés:\n"
        "- Sélection des strikes (ex: SPY $520)\n"
        "- Gestion des risques\n"
        "- Profit cible/stop loss\n"
        "Sois concis et pragmatique."
    )
    
    print(f"\n📝 Prompt de test:\n{test_prompt}")
    
    # Liste des modèles réellement disponibles et fiables
    models_to_test = [
        "mistralai/mistral-7b-instruct:free",       # Toujours fiable
        "mistralai/mistral-small-3.1-24b-instruct:free",  # Version plus puissante
        "gryphe/mythomax-l2-13b:free"               # Retesté avec nom corrigé
    ]
    
    # Tester les modèles
    for model in models_to_test:
        print(f"\n{'='*60}")
        success = test_model(model, test_prompt)
        if success:
            print(f"\n🔥 Test réussi avec {model}!")
        else:
            print(f"\n⚠️ Échec avec {model}")
        
        time.sleep(1)  # Pause entre les tests

    print("\n💡 Conseil: Mistral 7B est le plus fiable pour les requêtes trading")



