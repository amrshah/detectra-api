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
# New: Environment variable for semicolon-separated download links
CUSTOM_MODEL_URLS = os.getenv("MODEL_DOWNLOAD_URLS", "")

# Default URLs provided by user
DEFAULT_MODEL_URLS = [
    "https://huggingface.co/Musawer14/fight_detection_yolov8/resolve/main/Yolo_nano_weights.pt?download=true",
    "https://huggingface.co/Musawer14/fight_detection_yolov8/resolve/main/yolo_small_weights.pt?download=true",
    "https://github.com/Rohit-raj-t/Violence-detection/blob/main/yolov8n.pt"
]

# --- Helpers ---
def download_model(url: str, overwrite: bool = False):
    """Downloads a model from a URL if missing or if overwrite is True."""
    # Clean up GitHub URLs for raw download
    if "github.com" in url and "/blob/" in url:
        url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    
    # Extract filename from URL
    filename = url.split('/')[-1].split('?')[0]
    if not filename.endswith('.pt'):
        filename = f"{filename}.pt" # Fallback extension
        
    local_path = os.path.join(MODEL_DIR, filename)
    
    if os.path.exists(local_path) and not overwrite:
        return local_path

    print(f"Downloading model from {url} to {local_path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded {filename}.")
        return local_path
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

# --- Startup Logic ---
@app.on_event("startup")
async def startup_event():
    if MOCK_MODE:
        print("!!! RUNNING IN MOCK MODE !!! models will not be loaded.")
        return

    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    
    # 1. Download Default Models (if missing)
    for url in DEFAULT_MODEL_URLS:
        download_model(url, overwrite=False)

    # 2. Download Custom Models from ENV (Always Overwrite as requested)
    if CUSTOM_MODEL_URLS:
        url_list = [u.strip() for u in CUSTOM_MODEL_URLS.split(';') if u.strip()]
        for url in url_list:
            download_model(url, overwrite=True)

    print("Startup model check complete.")

# Global model placeholders
yolo_model = None
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
        "models_status": {
            "directory_exists": os.path.exists(MODEL_DIR),
            "files": os.listdir(MODEL_DIR) if os.path.exists(MODEL_DIR) else []
        }
    }

@app.get("/models")
async def list_models(token: str = Depends(verify_auth)):
    """Lists files in the models directory and default source URLs."""
    local_files = os.listdir(MODEL_DIR) if os.path.exists(MODEL_DIR) else []
    return {
        "local_models": local_files,
        "default_sources": DEFAULT_MODEL_URLS,
        "custom_sources": CUSTOM_MODEL_URLS.split(';') if CUSTOM_MODEL_URLS else []
    }

@app.post("/download-default-models")
async def trigger_download(token: str = Depends(verify_auth)):
    """Manually triggers download of default models with overwrite enabled."""
    results = []
    for url in DEFAULT_MODEL_URLS:
        path = download_model(url, overwrite=True)
        results.append({"url": url, "success": path is not None})
    return {"status": "completed", "results": results}


@app.post("/detect-batch")
async def detect_batch(
    images: List[UploadFile] = File(...), 
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
