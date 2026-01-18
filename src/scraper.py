import os
import json
import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.types import Message, MessageMediaPhoto
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv('TG_API_ID')
API_HASH = os.getenv('TG_API_HASH')
PHONE = os.getenv('TG_PHONE')

# List of channels to scrape
CHANNELS: List[str] = [
    '@lobelia4cosmetics', 
    '@tikvahpharma', 
    '@DoctorsET'
]

# Directory Setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

os.makedirs(LOG_DIR, exist_ok=True)

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'scraper.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MedicalDataScraper:
    """
    A class to scrape text and images from public Telegram channels.
    """
    def __init__(self, client: TelegramClient):
        self.client = client

    async def download_image(self, message: Message, channel_name: str) -> Optional[str]:
        """
        Downloads image media from a message if present.

        Args:
            message (Message): The Telethon message object.
            channel_name (str): The name of the channel (used for folder naming).

        Returns:
            Optional[str]: The local file path of the downloaded image, or None.
        """
        if message.photo:
            try:
                image_dir = os.path.join(DATA_DIR, 'images', channel_name)
                os.makedirs(image_dir, exist_ok=True)
                
                filename = f"{message.id}.jpg"
                file_path = os.path.join(image_dir, filename)
                
                if not os.path.exists(file_path):
                    await self.client.download_media(message, file=file_path)
                return file_path
            except Exception as e:
                logger.error(f"Failed to download image for msg {message.id}: {e}")
                return None
        return None

    async def scrape_channel(self, channel_username: str, limit: int = 100) -> None:
        """
        Scrapes messages from a single channel and saves them to JSON.
        
        Args:
            channel_username (str): The Telegram handle (e.g., @channel).
            limit (int): Maximum number of messages to retrieve.
        """
        logger.info(f"Starting scrape for {channel_username}...")
        data_buffer: Dict[str, List[Dict[str, Any]]] = {}

        try:
            entity = await self.client.get_entity(channel_username)
            channel_title = entity.title
            clean_name = channel_username.strip('@')
            
            async for message in self.client.iter_messages(entity, limit=limit):
                if not message.date:
                    continue

                try:
                    msg_date_str = message.date.strftime('%Y-%m-%d')
                    image_path = await self.download_image(message, clean_name)

                    data_item = {
                        "message_id": message.id,
                        "channel_name": channel_username,
                        "channel_title": channel_title,
                        "message_date": message.date.isoformat(),
                        "message_text": message.text,
                        "has_media": bool(message.media),
                        "image_path": image_path,
                        "views": message.views or 0,
                        "forwards": message.forwards or 0,
                        "scraped_at": datetime.now().isoformat()
                    }

                    if msg_date_str not in data_buffer:
                        data_buffer[msg_date_str] = []
                    data_buffer[msg_date_str].append(data_item)

                except Exception as e:
                    logger.warning(f"Error processing message {message.id}: {e}")
                    continue

            self.save_data(data_buffer, clean_name)
            logger.info(f"Finished scraping {channel_username}.")

        except FloodWaitError as e:
            logger.error(f"Rate limited by Telegram. Must wait {e.seconds} seconds.")
            # In a real scheduler, we might sleep, but here we just log and exit
        except Exception as e:
            logger.error(f"Critical error scraping {channel_username}: {e}", exc_info=True)

    def save_data(self, data_buffer: Dict[str, List[Dict]], channel_name: str) -> None:
        """Saves buffered data to partitioned JSON files."""
        for date_key, messages in data_buffer.items():
            target_dir = os.path.join(DATA_DIR, 'telegram_messages', date_key)
            os.makedirs(target_dir, exist_ok=True)
            
            file_path = os.path.join(target_dir, f"{channel_name}.json")
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(messages, f, ensure_ascii=False, indent=4)
            except IOError as e:
                logger.error(f"Failed to write file {file_path}: {e}")

async def main():
    client = TelegramClient('medical_scraper_session', API_ID, API_HASH)
    await client.start(phone=PHONE)
    
    scraper = MedicalDataScraper(client)
    
    for channel in CHANNELS:
        await scraper.scrape_channel(channel, limit=200)

if __name__ == '__main__':
    asyncio.run(main())