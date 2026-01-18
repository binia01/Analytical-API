# Analytical-API

## Task 1: Data Scraping and Collection Pipeline

This module is responsible for extracting medical-related data from specified Telegram channels. It collects text messages, metadata, and images, organizing them into a structured format suitable for further analysis.

### Features
- **Telegram Scraping**: Connects to the Telegram API using Telethon.
- **Multi-channel Support**: Scrapes data from multiple pre-defined channels (`@CheMed123`, `@lobelia4cosmetics`, etc.).
- **Data Partitioning**: Organizes collected messages by date (`YYYY-MM-DD`).
- **Image Handling**: Downloads and links images associated with messages.
- **Logging**: Tracks the scraping process and errors in `logs/scraper.log`.

### Prerequisites
1. **Python 3.x**: Ensure Python is installed.
2. **Telegram API Credentials**:
   - Obtain `API_ID` and `API_HASH` from [my.telegram.org](https://my.telegram.org).
   - A valid phone number for authentication.

### Setup
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Create a `.env` file in the root directory with the following content:
   ```env
   APP_API_ID=your_api_id
   APP_API_HASH=your_api_hash
   APP_PHONE=your_phone_number
   ```

### Usage
To start the scraping process, run the scraper script from the project root:

```bash
python src/scraper.py
```

On the first run, you will be prompted to enter the authentication code sent to your Telegram account.

### Output Structure
The scraped data is stored in the `data/raw/` directory:

- **Messages**: `data/raw/telegram_messages/YYYY-MM-DD/{channel_name}.json`
- **Images**: `data/raw/images/{channel_name}/{message_id}.jpg`
- **Logs**: `logs/scraper.log`
