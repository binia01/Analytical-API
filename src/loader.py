import os
import json
import pandas as pd
from sqlalchemy import create_engine, text 
from dotenv import load_dotenv

load_dotenv()

# DB Connection
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "medical_warehouse")

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def load_raw_data():
    # Construct path to data directory
    base_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        'data', 'raw', 'telegram_messages'
    )
    
    all_messages = []

    # Iterate through date folders and channel files
    if not os.path.exists(base_dir):
        print(f"No data directory found at: {base_dir}")
        return

    for date_folder in os.listdir(base_dir):
        date_path = os.path.join(base_dir, date_folder)
        if os.path.isdir(date_path):
            for filename in os.listdir(date_path):
                if filename.endswith(".json"):
                    file_path = os.path.join(date_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Append list of messages
                        if isinstance(data, list):
                            all_messages.extend(data)
                        else:
                            all_messages.append(data)

    if not all_messages:
        print("No messages found to load.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(all_messages)
    
    print(f"Loading {len(df)} rows into PostgreSQL...")
    
    engine = create_engine(DB_URL)
    
    # Load to 'raw' schema (create if not exists)
    with engine.connect() as connection:
        # --- FIX: Wrapped string in text() and added commit() ---
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        connection.commit() 
        
    # Write data to SQL
    df.to_sql('telegram_messages', engine, schema='raw', if_exists='replace', index=False)
    print("Data loaded successfully to raw.telegram_messages")

if __name__ == "__main__":
    load_raw_data()