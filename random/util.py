import requests
from datetime import datetime
import time
import json

class JupiterMonitor:
    def __init__(self, volume_threshold_usd=1000):
        self.jupiter_api_url = "https://price.jup.ag/v4/token-list"
        self.jupiter_pairs_url = "https://stats.jup.ag/coingecko/pairs"
        self.volume_threshold = volume_threshold_usd
        self.max_age_minutes = 5

    def get_token_list(self):
        """Get list of tokens from Jupiter"""
        try:
            response = requests.get(self.jupiter_api_url)
            if response.status_code == 200:
                return response.json().get('data', [])
            else:
                print(f"Error: Jupiter API returned status {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting token list: {e}")
            return []

    def get_pairs_data(self):
        """Get pairs data from Jupiter"""
        try:
            response = requests.get(self.jupiter_pairs_url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error: Jupiter pairs API returned status {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting pairs data: {e}")
            return []

    def get_token_info(self, token_address):
        """Get detailed token information from Jupiter"""
        try:
            url = f"https://stats.jup.ag/coingecko/tokens/{token_address}"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting token info: {e}")
            return None

    def scan_new_pairs(self):
        """Scan for new pairs with specified volume"""
        print(f"Scanning for pairs with minimum volume of ${self.volume_threshold:,.2f}...")

        try:
            # Get pairs data
            pairs_data = self.get_pairs_data()
            
            # Get token list for additional information
            tokens = {token['address']: token for token in self.get_token_list()}
            
            # Filter and process pairs
            new_high_volume_pairs = []
            
            for pair in pairs_data:
                try:
                    # Get volume
                    volume_24h = float(pair.get('volume24h', 0))
                    
                    # Skip if volume doesn't meet threshold
                    if volume_24h < self.volume_threshold:
                        continue

                    # Get token details
                    token_address = pair.get('baseToken', {}).get('address')
                    if not token_address:
                        continue

                    token_info = self.get_token_info(token_address)
                    if not token_info:
                        continue

                    # Get detailed information
                    pair_info = {
                        'name': token_info.get('name', 'Unknown'),
                        'symbol': token_info.get('symbol', 'Unknown'),
                        'address': token_address,
                        'volume_24h': volume_24h,
                        'price_usd': float(pair.get('priceUsd', 0)),
                        'liquidity_usd': float(pair.get('liquidity', {}).get('usd', 0)),
                        'holder_count': token_info.get('holder_count', 0),
                        'market_cap': token_info.get('market_cap', 0),
                        'dexes': pair.get('dexes', []),
                        'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Jupiter doesn't provide creation time
                    }

                    new_high_volume_pairs.append(pair_info)
                    
                    # Print pair information
                    print("\nHigh Volume Token Found!")
                    print(f"Name: {pair_info['name']} ({pair_info['symbol']})")
                    print(f"Address: {pair_info['address']}")
                    print(f"Volume (24h): ${pair_info['volume_24h']:,.2f}")
                    print(f"Price: ${pair_info['price_usd']:.8f}")
                    print(f"Liquidity: ${pair_info['liquidity_usd']:,.2f}")
                    print(f"Market Cap: ${pair_info['market_cap']:,.2f}")
                    print(f"Holder Count: {pair_info['holder_count']:,}")
                    print(f"Available on: {', '.join(pair_info['dexes'])}")
                    print(f"Birdeye: https://birdeye.so/token/{pair_info['address']}")
                    print("-" * 50)
                
                except Exception as e:
                    print(f"Error processing pair: {e}")
                    continue
            
            return new_high_volume_pairs

        except Exception as e:
            print(f"Error scanning pairs: {e}")
            return []

def main():
    # Set volume threshold (in USD)
    VOLUME_THRESHOLD = 100  # $100 minimum volume
    monitor = JupiterMonitor(volume_threshold_usd=VOLUME_THRESHOLD)
    
    start_time = time.time()
    new_pairs = monitor.scan_new_pairs()
    end_time = time.time()
    
    print(f"\nScan completed in {end_time - start_time:.2f} seconds")
    print(f"Found {len(new_pairs)} high-volume pairs")

if __name__ == "__main__":
    main()