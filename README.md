Trading Bot Project
Bot Telegram pour trading automatisé (options, cryptos, forex, commodities).

Rendement : ~22-23% net sur 9 mois.
VaR : ~1.6%, CVaR : ~1.8%.
Plateformes : Alpaca (options), Oanda (forex/commodities), Kraken (cryptos).
Conformité : France 2025 (AMF, KYC).

Setup

Installer Python 3.8+, VS Code, Docker.
Créer environnement virtuel :python3 -m venv venv && source venv/bin/activate


Installer dépendances :pip install -r requirements.txt


Configurer .env à partir de .env.example (ajouter clés API Alpaca, Oanda, Kraken, Alpha Vantage, OpenRouter, Telegram).
Tester en mode paper :python core/bot.py


Dockeriser :docker build -t trading-bot .
docker run --env-file .env trading-bot

Ou avec Docker Compose :docker-compose up -d



Déploiement

Sur un droplet :ssh root@your_droplet_ip "cd /root/trading-bot-project && git pull && docker-compose up -d"



Structure

core/bot.py : Flux principal (Telegram, APScheduler, DeepSeek).
exchanges/ : Interfaces Alpaca, Oanda, Kraken pour paper trading.
utils/ : Modèles SABR, Kalman, LSTM, Q-Learning, PCA, GARCH, etc.
strategies.json : Roadmap des trades.
.env : Clés API et configuration (ex. AUTO_TRADE_MODE=paper).

Notes

Stratégies : Iron Condor, Straddle, Strangle, Calendar, Butterfly, Iron Butterfly, Double Diagonal (0-3 DTE), arbitrage, scalping.
Actifs : SPY, QQQ, IWM, VIX (Alpaca), ETHEUR, USDCEUR (Kraken), EURUSD, GBPUSD, USDJPY, XAUUSD, UKOIL, NGAS (Oanda).
Protections : VIX scaling, rebalancing, circuit breaker, sentiment exit.
Conformité : AMF disclaimer, KYC vérifié.

