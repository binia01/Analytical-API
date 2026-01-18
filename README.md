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

## Task 2: Data Cleaning and Transformation (ELT)

This module handles the loading of raw scraped data into a centralized database and performs transformations using **dbt** (data build tool) to prepare the data for analysis.

### Features
- **Data Loading**: `src/loader.py` reads the raw JSON files from Task 1, flattens the structure, and loads them into a PostgreSQL database in the `raw` schema.
- **Data Transformation (dbt)**:
  - **Staging**: Cleans and standardizes raw data (`stg_telegram_messages`).
  - **Data Marts**: Implements a Star Schema for analytical queries:
    - `dim_channels`: Dimension table for channel information.
    - `dim_dates`: Dimension table for time-based analysis.
    - `fct_messages`: Fact table containing message metrics.

### Prerequisites
1. **PostgreSQL**: A running PostgreSQL instance.
2. **dbt**: Installed via requirements (`dbt-postgres`).

### Configuration
Add the following database credentials to your `.env` file:

```env
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=medical_warehouse
```

### Usage

1. **Load Raw Data**:
   Run the loader script to populate the database:
   ```bash
   python src/loader.py
   ```

2. **Run dbt Transformations**:
   Navigate to the dbt project directory and run the models:
   ```bash
   cd medical_warehouse
   dbt deps  # Install dependencies (if any)
   dbt run   # Run models
   dbt test  # Run data quality tests
   ```

### Data Model
The transformation pipeline produces the following structure:
- **Raw Layer**: `raw.telegram_messages` (Flat load of JSONs)
- **Staging Layer**: `public.stg_telegram_messages` (Cleaned views)
- **Serving Layer**: `public.fct_messages`, `public.dim_channels`


