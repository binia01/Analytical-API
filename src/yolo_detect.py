import os
import pandas as pd
from ultralytics import YOLO
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


MODEL_PATH = 'yolov8n.pt' 
IMAGES_DIR = os.path.join('data', 'raw', 'images')
DB_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@" \
         f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

def get_image_category(detected_objects):
    """
    Classifies image based on detected objects.
    Logic:
    - Person + Container (bottle/cup) -> Promotional (someone showing product)
    - Container only -> Product Display
    - Person only -> Lifestyle
    - Else -> Other
    """
    has_person = 'person' in detected_objects
    # YOLO class names for containers
    has_product = any(item in detected_objects for item in ['bottle', 'cup', 'bowl', 'wine glass'])
    
    if has_person and has_product:
        return 'promotional'
    elif has_product:
        return 'product_display'
    elif has_person:
        return 'lifestyle'
    else:
        return 'other'

def run_detection():
    print("Loading YOLO model...")
    model = YOLO(MODEL_PATH)
    
    records = []
    
    # Walk through channel folders
    if not os.path.exists(IMAGES_DIR):
        print(f"Image directory {IMAGES_DIR} not found.")
        return

    print("Starting detection scan (this may take a while)...")
    
    for channel_name in os.listdir(IMAGES_DIR):
        channel_path = os.path.join(IMAGES_DIR, channel_name)
        if not os.path.isdir(channel_path):
            continue
            
        for img_file in os.listdir(channel_path):
            if not img_file.endswith(('.jpg', '.png', '.jpeg')):
                continue
                
            img_path = os.path.join(channel_path, img_file)
            message_id = img_file.split('.')[0] # Filename is message_id.jpg
            
            try:
                # Run Inference
                results = model(img_path, verbose=False)
                result = results[0]
                
                # Extract detected classes
                detected_classes = []
                confidences = []
                
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    conf = float(box.conf[0])
                    
                    detected_classes.append(class_name)
                    confidences.append(conf)
                
                # Determine Category
                category = get_image_category(detected_classes)
                
                records.append({
                    'message_id': int(message_id),
                    'channel_name': channel_name,
                    'image_path': img_path,
                    'detected_objects': detected_classes, # Store as list/array
                    'avg_confidence': sum(confidences)/len(confidences) if confidences else 0,
                    'image_category': category
                })
                
            except Exception as e:
                print(f"Error processing {img_path}: {e}")

    # Save to DB
    if records:
        df = pd.DataFrame(records)
        
        # Convert list to string for simple SQL storage (or use ARRAY if you prefer)
        df['detected_objects'] = df['detected_objects'].apply(lambda x: ','.join(x))
        
        print(f"Detected objects in {len(df)} images. Loading to Database...")
        
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
            print("Dropping old table and dependent views...")
            conn.execute(text("DROP TABLE IF EXISTS raw.yolo_detections CASCADE;"))
            conn.commit()
            
        df.to_sql('yolo_detections', engine, schema='raw', if_exists='replace', index=False)
        print("Success! Data loaded to raw.yolo_detections")
    else:
        print("No images processed.")

if __name__ == "__main__":
    run_detection()