import os
import json
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# DB Configuration
DB_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@" \
         f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

def load_raw_data() -> None:
    """
    Reads JSON files from the Data Lake and loads them into PostgreSQL (raw schema).
    """
    base_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        'data', 'raw', 'telegram_messages'
    )
    
    if not os.path.exists(base_dir):
        logger.error(f"Data directory not found: {base_dir}")
        return

    all_messages = []

    # Traverse Data Lake
    for date_folder in os.listdir(base_dir):
        date_path = os.path.join(base_dir, date_folder)
        if os.path.isdir(date_path):
            for filename in os.listdir(date_path):
                if filename.endswith(".json"):
                    file_path = os.path.join(date_path, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                all_messages.extend(data)
                            else:
                                all_messages.append(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode JSON {file_path}: {e}")

    if not all_messages:
        logger.warning("No data found to load.")
        return

    df = pd.DataFrame(all_messages)
    logger.info(f"Prepared {len(df)} rows for loading.")

    try:
        engine = create_engine(DB_URL)
        with engine.connect() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
            connection.commit()
        
        df.to_sql('telegram_messages', engine, schema='raw', if_exists='replace', index=False)
        logger.info("Successfully loaded data into raw.telegram_messages")
        
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during loading: {e}")

if __name__ == "__main__":
    load_raw_data()