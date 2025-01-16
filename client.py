import os
import requests
from typing import List, Dict, Union, Optional
from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()

# Get variables from .env
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramClient:
    
    def __init__(self, bot_token: Optional[str] = None):

        self.bot_token = bot_token or os.getenv('BOT_TOKEN')
        if not self.bot_token:
            raise ValueError("Bot token must be provided or set in BOT_TOKEN environment variable")
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.session = requests.Session()

    def _make_request(self, method: str, **kwargs) -> Dict:

        try:
            response = self.session.post(
                f"{self.api_url}/{method}",
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            logger.error(f"Error in API request to {method}: {e}")
            raise

    def get_updates(self) -> List[Dict]:
  
        try:
            response = self.session.get(f"{self.api_url}/getUpdates")
            response.raise_for_status()
            updates = response.json()['result']
            
            return [{
                'chat_id': update['message']['chat']['id'],
                'username': update['message']['chat'].get('username'),
                'date': datetime.fromtimestamp(update['message']['date'])
            } for update in updates if 'message' in update]
            
        except requests.RequestException as e:
            logger.error(f"Error getting updates: {e}")
            raise

    def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: str = 'HTML',
        disable_preview: bool = False
    ) -> Dict:

        return self._make_request(
            'sendMessage',
            json={
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': disable_preview
            }
        )

    def send_message_with_buttons(
        self,
        chat_id: Union[int, str],
        text: str,
        buttons: List[List[Dict]],
        parse_mode: str = 'HTML',
        disable_preview: bool = False
    ) -> Dict:
      
        return self._make_request(
            'sendMessage',
            json={
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': disable_preview,
                'reply_markup': {
                    'inline_keyboard': buttons
                }
            }
        )

    def send_token_alert(
        self,
        chat_id: Union[int, str],
        token_data: Dict,
        disable_preview: bool = True
    ) -> Dict:
 
        message_text = f"""🔥 <b>New Token Alert!</b>

Name: {token_data.get('name', 'N/A')}
Symbol: {token_data.get('symbol', 'N/A')}
Price: ${token_data.get('price', '0.0')}
Liquidity: ${token_data.get('liquidity', '0.0')}
Change 24h: {token_data.get('change_24h', '0')}%

<a href="{token_data.get('trade_url', '#')}">Trade Now</a>"""

        buttons = [[
            {"text": "📊 Chart", "url": token_data.get('chart_url', '#')},
            {"text": "💱 Trade", "url": token_data.get('trade_url', '#')}
        ]]

        return self.send_message_with_buttons(
            chat_id,
            message_text,
            buttons,
            disable_preview=disable_preview
        )

    def broadcast_message(
        self,
        chat_ids: List[Union[int, str]],
        text: str,
        **kwargs
    ) -> List[Dict]:
  
        results = []
        for chat_id in chat_ids:
            try:
                result = self.send_message(chat_id, text, **kwargs)
                results.append({
                    'chat_id': chat_id,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                logger.error(f"Error broadcasting to {chat_id}: {e}")
                results.append({
                    'chat_id': chat_id,
                    'success': False,
                    'error': str(e)
                })
        return results

# Example usage
if __name__ == "__main__":
    
    # Yes
    client = TelegramClient(BOT_TOKEN)
    
    try:
        # Example token alert
        token_data = {
            "name": "Example Token",
            "symbol": "EXT",
            "price": "0.0001",
            "liquidity": "50000",
            "change_24h": "+15",
            "trade_url": "https://example.com/trade",
            "chart_url": "https://example.com/chart"
        }
        
        # Send token alert
        response = client.send_token_alert(CHAT_ID, token_data)
        print("Alert sent:", response)
        
    except Exception as e:
        logger.error(f"Error in example: {e}")

