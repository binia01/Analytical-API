import os
import json
import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import MessageMediaPhoto
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("APP_API_ID")
API_HASH = os.getenv("APP_API_HASH")
PHONE = os.getenv("APP_PHONE")

CHANNELS = [
    "@CheMed123",
    "@lobelia4cosmetics",
    "@tikvahpharma",
    "@Thequorachannel",
    "@tenamereja"
]

# Directory Setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure directories exist
os.makedirs(LOG_DIR, exist_ok=True)

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'scraper.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MedicalDataScraper:
    def __init__(self, client):
        self.client = client

    async def download_image(self, message, channel_name):
        """
        Downloads image if present and returns the relative path.
        Structure: data/raw/images/{channel_name}/{message_id}.jpg
        """
        if message.photo:
            # Create specific folder for this channel's images
            image_dir = os.path.join(DATA_DIR, 'images', channel_name)
            os.makedirs(image_dir, exist_ok=True)
            
            filename = f"{message.id}.jpg"
            file_path = os.path.join(image_dir, filename)
            
            # Download
            await self.client.download_media(message, file=file_path)
            return file_path
        return None

    async def scrape_channel(self, channel_username, limit=100):
        """
        Scrapes messages from a single channel and partitions data by date.
        """
        logger.info(f"Starting scrape for {channel_username}...")
        
        # Buffer to hold messages grouped by date: {'2024-01-01': [msg1, msg2]}
        data_buffer = {}

        try:
            entity = await self.client.get_entity(channel_username)
            channel_title = entity.title
            
            # Iterate through messages
            async for message in self.client.iter_messages(entity, limit=limit):
                if not message.date:
                    continue

                msg_date_str = message.date.strftime('%Y-%m-%d')
                
                # Download image if exists
                image_path = await self.download_image(message, channel_username.strip('@'))

                # Extract Data
                data_item = {
                    "message_id": message.id,
                    "channel_name": channel_username,
                    "channel_title": channel_title,
                    "message_date": message.date.isoformat(),
                    "message_text": message.text,
                    "has_media": bool(message.media),
                    "image_path": image_path,
                    "views": message.views if message.views else 0,
                    "forwards": message.forwards if message.forwards else 0,
                    "scraped_at": datetime.now().isoformat()
                }

                # Group by date for the Data Lake partition
                if msg_date_str not in data_buffer:
                    data_buffer[msg_date_str] = []
                data_buffer[msg_date_str].append(data_item)

            # Write buffer to JSON files
            self.save_data(data_buffer, channel_username.strip('@'))
            logger.info(f"Finished scraping {channel_username}.")

        except Exception as e:
            logger.error(f"Error scraping {channel_username}: {str(e)}")

    def save_data(self, data_buffer, channel_name):
        """
        Saves buffered data into partitioned JSON files.
        Structure: data/raw/telegram_messages/YYYY-MM-DD/channel_name.json
        """
        for date_key, messages in data_buffer.items():
            # Create folder for the specific date
            target_dir = os.path.join(DATA_DIR, 'telegram_messages', date_key)
            os.makedirs(target_dir, exist_ok=True)
            
            file_path = os.path.join(target_dir, f"{channel_name}.json")
            
            # Write to JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Saved {len(messages)} messages to {file_path}")

async def main():
    # Initialize Client
    client = TelegramClient('medical_scraper_session', API_ID, API_HASH)
    
    await client.start(phone=PHONE)
    
    # Verify Authentication
    if not await client.is_user_authorized():
        logger.info("Client not authorized. Sending code request...")
        await client.send_code_request(PHONE)
        try:
            await client.sign_in(PHONE, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password=input('Password: '))
    
    logger.info("Client Authenticated. Starting Scraper...")
    
    scraper = MedicalDataScraper(client)
    
    # Run scraping for all channels
    for channel in CHANNELS:
        await scraper.scrape_channel(channel, limit=500) # Limit set for testing

    logger.info("Scraping Job Completed.")

if __name__ == '__main__':
    # Telethon runs on an event loop
    asyncio.run(main())