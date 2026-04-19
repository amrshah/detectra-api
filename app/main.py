import os
import io
import torch
import requests
from typing import List, Annotated
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header, Form
from PIL import Image
from pydantic import BaseModel

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.models import Response

security = HTTPBearer()

app = FastAPI(
    title="Violence Detection API", 
    version="1.0.0",
    description="Backend API for real-time violence and weapon detection in image frames."
)

# --- Configuration ---
AUTH_KEY = os.getenv("AUTH_KEY", "default-secret-key")
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
MODEL_DIR = "models"
YOLO_MODEL_PATH = os.path.join(MODEL_DIR, "yolo.pt")
VIOLENCE_MODEL_PATH = os.path.join(MODEL_DIR, "violence.pt")

# URLs for weight downloads
YOLO_URL = "https://github.com/ultralytics/yolov5/releases/download/v6.0/yolov5n.pt"

# --- Startup Logic ---
@app.on_event("startup")
async def startup_event():
    if MOCK_MODE:
        print("!!! RUNNING IN MOCK MODE !!! models will not be loaded.")
        return

    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    
    # Download YOLO if missing
    if not os.path.exists(YOLO_MODEL_PATH):
        print(f"Downloading YOLOv5n weights from {YOLO_URL}...")
        try:
            response = requests.get(YOLO_URL)
            with open(YOLO_MODEL_PATH, "wb") as f:
                f.write(response.content)
            print("YOLO weights downloaded successfully.")
        except Exception as e:
            print(f"Failed to download YOLO weights: {e}")

    # Load Models
    global yolo_model, violence_model
    try:
        print("Loading YOLOv5 model...")
        yolo_model = torch.hub.load('ultralytics/yolov5', 'custom', path=YOLO_MODEL_PATH, force_reload=False)
        print("YOLOv5 model loaded.")
    except Exception as e:
        print(f"Error loading YOLOv5 model: {e}")
        yolo_model = None

    try:
        if os.path.exists(VIOLENCE_MODEL_PATH):
            print("Loading Violence model...")
            violence_model = torch.jit.load(VIOLENCE_MODEL_PATH)
            violence_model.eval()
            print("Violence model loaded.")
        else:
            print(f"WARNING: Violence model not found at {VIOLENCE_MODEL_PATH}.")
            violence_model = None
    except Exception as e:
        print(f"Error loading Violence model: {e}")
        violence_model = None

# --- Helpers ---
def verify_auth(auth: HTTPAuthorizationCredentials = Depends(security)):
    if auth.credentials != AUTH_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return auth.credentials

def get_mock_response(filename: str):
    import random
    # Simulate a mix of results
    has_weapon = random.random() > 0.7
    weapons = []
    if has_weapon:
        weapons.append({
            "type": random.choice(["knife", "gun", "pistol"]),
            "confidence": round(random.uniform(0.7, 0.99), 4),
            "box": [100.0, 150.0, 300.0, 450.0]
        })
    
    violence_prob = random.uniform(0.1, 0.9)
    violence_detected = violence_prob > 0.5
    
    has_gun = any(w["type"] in ["gun", "pistol"] for w in weapons)
    shooting = has_gun and violence_prob > 0.6
    
    return {
        "filename": filename,
        "weapons": weapons,
        "violence": {
            "detected": violence_detected,
            "confidence": round(violence_prob, 4)
        },
        "critical_event": {
            "shooting": shooting
        },
        "alert": shooting or violence_detected or len(weapons) > 0,
        "mock": True
    }

def preprocess_for_violence(img: Image.Image):
    img = img.resize((224, 224))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    t = torch.tensor(list(img.getdata())).float()
    t = t.view(224, 224, 3).permute(2, 0, 1) / 255.0
    return t.unsqueeze(0)

def detect_weapons(img: Image.Image):
    if yolo_model is None:
        return []
    results = yolo_model(img)
    detections = []
    for *box, conf, cls in results.xyxy[0]:
        label = yolo_model.names[int(cls)]
        if label in ["knife", "scissors", "gun", "pistol", "firearm"]:
            detections.append({
                "type": label,
                "confidence": round(float(conf), 4),
                "box": [round(float(x), 2) for x in box]
            })
    return detections

def classify_violence(img: Image.Image):
    if violence_model is None:
        return 0.0
    tensor = preprocess_for_violence(img)
    with torch.no_grad():
        out = violence_model(tensor)
        prob = torch.sigmoid(out).item()
    return prob

# --- API Endpoints ---

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "mock_mode": MOCK_MODE,
        "models": {
            "yolo": "loaded" if (not MOCK_MODE and yolo_model) else ("mocked" if MOCK_MODE else "missing"),
            "violence": "loaded" if (not MOCK_MODE and violence_model) else ("mocked" if MOCK_MODE else "missing")
        }
    }


@app.post("/detect-batch")
async def detect_batch(
    images: Annotated[List[UploadFile], File(...)], 
    token: str = Depends(verify_auth)
):
    if len(images) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 images allowed per batch")

    batch_results = []
    
    for file in images:
        if MOCK_MODE:
            batch_results.append(get_mock_response(file.filename))
            continue

        try:
            contents = await file.read()
            if len(contents) > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"File {file.filename} is too large (> 5MB)")

            img = Image.open(io.BytesIO(contents))
            
            weapons = detect_weapons(img)
            violence_prob = classify_violence(img)
            violence_detected = violence_prob > 0.5
            
            has_gun = any(w["type"] in ["gun", "pistol", "firearm"] for w in weapons)
            shooting = has_gun and violence_prob > 0.6
            
            alert = shooting or violence_detected or len(weapons) > 0
            
            batch_results.append({
                "filename": file.filename,
                "weapons": weapons,
                "violence": {
                    "detected": violence_detected,
                    "confidence": round(violence_prob, 4)
                },
                "critical_event": {
                    "shooting": shooting
                },
                "alert": alert
            })
            
        except Exception as e:
            batch_results.append({
                "filename": file.filename,
                "error": str(e)
            })

    # Aggregated Result (Majority Vote)
    alerts_count = sum(1 for r in batch_results if r.get("alert", False))
    final_alert = alerts_count >= (len(batch_results) // 2 + 1) if batch_results else False

    return {
        "results": batch_results,
        "aggregated": {
            "alert": final_alert,
            "total_alerts": alerts_count,
            "method": "majority_vote"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4141)
