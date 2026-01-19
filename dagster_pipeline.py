import os
import subprocess
from dagster import job, op, ScheduleDefinition, file_relative_path

# --- Helpers ---
def run_command(command, cwd=None):
    """Runs a shell command and raises error if it fails."""
    result = subprocess.run(
        command, 
        cwd=cwd, 
        shell=True, 
        capture_output=True, 
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Command failed: {command}\nError: {result.stderr}")
    return result.stdout

# --- Ops (The Steps) ---

@op
def scrape_telegram_data(context):
    """Step 1: Run the Telethon Scraper"""
    context.log.info("Starting Scraper...")
    # Pointing to the script in scripts/scraper.py
    script_path = os.path.join("src", "scraper.py")
    output = run_command(f"python {script_path}")
    context.log.info(output)

@op
def load_raw_to_postgres(context, start_trigger):
    """Step 2: Load JSON data into PostgreSQL"""
    context.log.info("Loading JSON to DB...")
    script_path = os.path.join("src", "loader.py")
    output = run_command(f"python {script_path}")
    context.log.info(output)
    return "raw_data_loaded"

@op
def run_yolo_enrichment(context, start_trigger):
    """Step 3: Run YOLO Object Detection"""
    context.log.info("Running YOLO Detection...")
    # Assuming you moved yolo_detect.py to scripts/ or src/
    # Adjust this path if your yolo script is in src/
    script_path = os.path.join("src", "yolo_detect.py") 
    
    if os.path.exists(script_path):
        output = run_command(f"python {script_path}")
        context.log.info(output)
    else:
        context.log.warn(f"YOLO script not found at {script_path}, skipping.")
    return "yolo_done"

@op
def run_dbt_transformations(context, yolo_done, raw_loaded):
    """Step 4: Run dbt (Only runs after Load AND YOLO are done)"""
    context.log.info("Running dbt models...")
    dbt_dir = file_relative_path(__file__, "medical_warehouse")
    
    # 1. dbt deps (ensure packages are installed)
    run_command("dbt deps", cwd=dbt_dir)
    
    # 2. dbt run
    output = run_command("dbt run", cwd=dbt_dir)
    context.log.info(output)
    
    # 3. dbt test
    test_output = run_command("dbt test", cwd=dbt_dir)
    context.log.info(test_output)

# --- Job (The Flow) ---

@job
def medical_pipeline_job():
    # 1. Scrape
    scraped = scrape_telegram_data()
    
    # 2. Load and YOLO run in parallel (or sequential) after Scraping
    # We pass 'scraped' to ensure they wait for scraping to finish
    raw_loaded = load_raw_to_postgres(start_trigger=scraped)
    yolo_done = run_yolo_enrichment(start_trigger=scraped)
    
    # 3. Run dbt only after BOTH loading and YOLO are finished
    run_dbt_transformations(yolo_done=yolo_done, raw_loaded=raw_loaded)

# --- Schedule (Daily at Midnight) ---

daily_schedule = ScheduleDefinition(
    job=medical_pipeline_job,
    cron_schedule="0 0 * * *",  # Daily at midnight
)