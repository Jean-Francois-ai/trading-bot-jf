# trading_bot_llm_comparison_fixed.py
from openai import OpenAI
import json
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
        print(f"✅ Connectivité: HTTP {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Échec de connexion: {str(e)}")
        return False

# Test d'un modèle avec gestion des réponses incomplètes
def test_model(model_name, prompt, max_retries=2):
    print(f"\n🚀 Début du test pour: {model_name}")
    client = OpenAI(base_url=OPENROUTER_URL, api_key=API_KEY)
    
    for attempt in range(max_retries):
        try:
            print(f"  Tentative {attempt+1}/{max_retries}...")
            start_time = time.time()
            
            # Gestion spéciale pour deepseek-v3-base
            actual_model = model_name
            if "v3-base" in model_name:
                print("⚠️ Remplacement de deepseek-v3-base par deepseek-r1 (plus fiable)")
                actual_model = "deepseek/deepseek-r1:free"
            
            response = client.chat.completions.create(
                model=actual_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400,  # Augmenté pour éviter les troncatures
                timeout=30
            )
            
            elapsed_time = time.time() - start_time
            content = response.choices[0].message.content.strip() if response.choices else ""
            
            if content:
                # Vérifie si la réponse est complète
                is_complete = "###FIN###" in content
                content = content.replace("###FIN###", "").strip()
                
                return {
                    "success": True,
                    "model": model_name,
                    "actual_model": actual_model,
                    "time": elapsed_time,
                    "content": content,
                    "complete": is_complete,
                    "tokens": response.usage.total_tokens,
                    "finish_reason": response.choices[0].finish_reason
                }
                
        except Exception as e:
            error = str(e)
            print(f"  ❌ Erreur: {error}")
            time.sleep(1.5 * (attempt + 1))
    
    return {
        "success": False,
        "model": model_name,
        "error": error if 'error' in locals() else "Réponse vide"
    }

# --- Programme principal ---
if __name__ == "__main__":
    print("="*60)
    print("COMPARAISON COMPLÈTE DE MODÈLES LLM POUR TRADING BOT")
    print("="*60)
    
    if not test_connectivity():
        exit(1)
    
    # Prompt optimisé avec instruction de fin
    test_prompt = (
        "Tu es un expert en trading algorithmique. "
        "Explique en 2 phrases MAXIMUM comment un RSI > 70 peut être utilisé "
        "dans une stratégie de trading. "
        "Important: "
        "1. Sois concis et précis "
        "2. Termine ta réponse par ###FIN### "
        "3. Ne donne PAS de conseil financier."
    )
    
    print(f"\n📝 Prompt de test:\n{test_prompt}")
    
    # Liste des modèles à comparer
    models_to_test = [
        "tngtech/deepseek-r1t2-chimera:free",   # DeepSeek Chimera
        "deepseek/deepseek-v3-base:free",        # DeepSeek V3 Base (sera remplacé)
        "mistralai/mistral-small-3.1-24b-instruct:free", # Mistral 24B
        "gryphe/mythomax-l2-13b:free"            # MythoMax (alternative)
    ]
    
    # Tester tous les modèles
    results = []
    for i, model in enumerate(models_to_test):
        print(f"\n{'='*40} TEST {i+1}/{len(models_to_test)} {'='*40}")
        result = test_model(model, test_prompt)
        results.append(result)
        time.sleep(1)  # Pause entre les modèles
    
    # Afficher les résultats comparatifs
    print("\n\n📊 RÉSULTATS COMPARATIFS")
    print("="*80)
    
    for res in results:
        if res['success']:
            status = "✅ COMPLET" if res['complete'] else "⚠️ INCOMPLET (marqueur ###FIN### manquant)"
            print(f"\n🔹 Modèle demandé: {res['model']}")
            if res['model'] != res.get('actual_model', ''):
                print(f"🔹 Modèle utilisé: {res['actual_model']}")
            print(f"⏱ Temps: {res['time']:.2f}s | Tokens: {res['tokens']} | {status}")
            print(f"📝 Réponse:\n{res['content']}")
            print("-"*80)
        else:
            print(f"\n❌ Échec avec {res['model']}: {res.get('error', 'Raison inconnue')}")
    
    # Statistiques
    success_count = sum(1 for res in results if res['success'])
    complete_count = sum(1 for res in results if res.get('complete', False))
    
    print(f"\n📈 STATISTIQUES FINALES")
    print(f"✅ {success_count}/{len(models_to_test)} modèles ont répondu")
    print(f"🟢 {complete_count} réponses complètes (avec ###FIN###)")
    print(f"⚠️ {success_count - complete_count} réponses incomplètes")
    
    # Trouver le modèle le plus rapide parmi ceux qui ont réussi
    successful_models = [res for res in results if res['success']]
    if successful_models:
        fastest = min(successful_models, key=lambda x: x['time'])
        print(f"⚡ Modèle le plus rapide: {fastest.get('actual_model', fastest['model'])} ({fastest['time']:.2f}s)")

# Exécutez ce code pour obtenir une comparaison complète!
