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

## Task 3: Object Detection using YOLO

This module applies Computer Vision techniques to analyze images collected from Telegram channels. It uses the YOLOv8 (You Only Look Once) model to detect objects and categorize images based on their content.

### Features
- **Object Detection**: Uses `ultralytics` YOLOv8n model to identify objects (persons, bottles, cups, etc.) in images.
- **Rule-Based Classification**: Categorizes images into business-relevant types based on detected objects:
  - **Promotional**: Contains both a person and a product container (bottle, cup, etc.).
  - **Product Display**: Contains only product containers.
  - **Lifestyle**: Contains only persons.
  - **Other**: No relevant objects detected.
- **Data Integration**: Detection results (bounding box classes, confidence scores) are stored in the database.

### Prerequisites
1. **YOLO Model**: Ensure `yolov8n.pt` is present in the project root (automatically downloaded by `ultralytics` if missing).
2. **Dependencies**: `ultralytics` package (included in `requirements.txt`).

### Usage

1. **Run Detection Script**:
   Process all images in `data/raw/images/` and save results to the database:
   ```bash
   python src/yolo_detect.py
   ```

2. **Run dbt Transformations**:
   After loading detection data, update the data warehouse models:
   ```bash
   cd medical_warehouse
   dbt run --select stg_yolo_detections fct_image_detections
   ```

### Data Model Extension
This task adds the following tables to the warehouse:
- **Raw**: `raw.yolo_detections` (Raw inference output)
- **Staging**: `stg_yolo_detections` (Cleaned detection data)
- **Serving**: `fct_image_detections` (Fact table for image analytics)

## Task 4: Exposing Data via REST API

This module provides a **FastAPI** application to expose the analyzed data to external clients. It queries the processed data in the `medical_warehouse` (PostgreSQL) and serves it via JSON endpoints.

### Features
- **FastAPI Framework**: High-performance, easy-to-use Python web framework.
- **Key Endpoints**:
  - `GET /api/reports/top-products`: Returns most frequently mentioned medical keywords.
  - `GET /api/channels/{channel_name}/activity`: Returns posting activity and view counts for a channel over time.
  - `GET /api/search/messages`: Full-text search for messages containing specific keywords (e.g., "Paracetamol").
- **Database Integration**: Connects directly to the `fct_messages` and Dimension tables for real-time analytics.
- **Documentation**: Automatic interactive API docs generated at `/docs`.

### Prerequisites
1. **Dependencies**: `fastapi`, `uvicorn`, `pydantic` (included in `requirements.txt`).
2. **Database**: PostgreSQL with simple text search enabled (default in Postgres).

### Usage

1. **Start the API Server**:
   Run the application using Uvicorn:
   ```bash
   uvicorn api.main:app --reload
   ```

2. **Access Documentation**:
   Open your browser and navigate to:
   - **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

3. **Sample Request**:
   Get top products/keywords:
   ```bash
   curl -X 'GET' \
     'http://127.0.0.1:8000/api/reports/top-products?limit=5' \
     -H 'accept: application/json'
   ```

## Task 5: Pipeline Orchestration & Automation

This module uses **Dagster** to orchestrate the entire data pipeline, ensuring that every step from scraping to transformation runs in the correct order and on schedule.

### Pipeline Workflow
The `medical_pipeline_job` defined in `pipeline.py` executes the following steps:
1.  **Scrape Data**: Runs the Telethon scraper (`src/scraper.py`) to fetch new messages.
2.  **Parallel Processing**:
    *   **Load Data**: Runs `src/loader.py` to ingest raw JSONs into PostgreSQL.
    *   **Image Analysis**: Runs `src/yolo_detect.py` to detect objects in images.
3.  **Transform Data**: Triggers **dbt** to clean and transform the data, but only after loading and detection are complete.

### Features
*   **Dependency Management**: Ensures dbt runs only when data is ready.
*   **Parallel Execution**: Speeds up the process by running independent tasks (Loader & YOLO) concurrently.
*   **Scheduling**: Includes a predefined schedule to run daily at midnight (`0 0 * * *`).
*   **Monitoring**: Dagster UI provides visual insights into pipeline runs, logs, and errors.

### Prerequisites
*   **Dagster**: `dagster` and `dagster-webserver` installed via `requirements.txt`.

### Usage

1.  **Launch Dagster UI**:
    Start the local development server:
    ```bash
    dagster dev -f pipeline.py
    ```

2.  **Trigger the Job**:
    *   Open [http://localhost:3000](http://localhost:3000) in your browser.
    *   Navigate to **Jobs** > **medical_pipeline_job**.
    *   Click **Launch Pad** and then **Launch Run**.

3.  **View Logs**:
    Track the progress of each step (Scrape -> Load/YOLO -> dbt) in the **Run Details** view.







