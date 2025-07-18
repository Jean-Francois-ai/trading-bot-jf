import requests
from dotenv import load_dotenv
import os
load_dotenv()

def liquidity_adjusted_alloc(exchange, symbol, base_alloc):
    depth_url = f"{exchange.base_url}/v2/stocks/{symbol}/snapshot" if 'alpaca' in exchange.base_url else f"{exchange.base_url}/api/v3/depth?symbol={symbol}"
    try:
        response = requests.get(depth_url)
        if response.ok:
            depth = response.json()
            bid_depth = sum(float(bid[1]) for bid in depth.get('bids', [])[:5]) if 'bids' in depth else float(depth.get('bid_size', 0))
            if bid_depth < float(os.getenv('LIQUIDITY_DEPTH_MIN', 100)):
                return base_alloc * 0.5
    except:
        pass
    return base_alloc
