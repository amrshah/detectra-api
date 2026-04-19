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

MAX_MODEL_SIZE = 500 * 1024 * 1024 # 500MB
MAX_MODELS = 6

def get_default_filenames():
    """Helper to get the filenames of the default models for preservation."""
    return [url.split('/')[-1].split('?')[0] for url in DEFAULT_MODEL_URLS]

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
        response = requests.get(url, stream=True, allow_redirects=True, timeout=30)
        response.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
        print(f"Successfully downloaded {filename} ({os.path.getsize(local_path)} bytes).")
        return local_path
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

class AddModelRequest(BaseModel):
    url: str
    overwrite: bool = True

# Global model management
loaded_models = {} # path -> model_object
model_errors = {}  # path -> error_string

def load_all_models():
    """Scans the models directory and loads all .pt files into memory."""
    global loaded_models, model_errors
    if MOCK_MODE:
        return
    
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)

    current_files = [f for f in os.listdir(MODEL_DIR) if f.endswith('.pt')]
    
    # Remove models no longer on disk
    for path in list(loaded_models.keys()):
        if os.path.basename(path) not in current_files:
            del loaded_models[path]
            model_errors.pop(path, None)

    # Load models
    for file in current_files:
        path = os.path.join(MODEL_DIR, file)
        
        # 500MB Size Check
        if os.path.getsize(path) > MAX_MODEL_SIZE:
            model_errors[path] = "File exceeds 500MB limit"
            continue

        if path not in loaded_models:
            print(f"Loading {file}...")
            try:
                # Attempt 1: Standard Torch Load (General)
                # We try Map Location to CPU for stability on VPS
                model = torch.load(path, map_location=torch.device('cpu'))
                # If it's a dict (common in YOLOv8/v5 saved weights), it's not the model itself
                if isinstance(model, dict) and 'model' in model:
                    model = model['model']
                
                model.eval()
                loaded_models[path] = model
                model_errors.pop(path, None)
                print(f"Successfully loaded {file} using torch.load")
                
            except Exception as e1:
                try:
                    # Attempt 2: YOLOv5 Hub Load
                    model = torch.hub.load('ultralytics/yolov5', 'custom', path=path, force_reload=False)
                    loaded_models[path] = model
                    model_errors.pop(path, None)
                    print(f"Successfully loaded {file} using YOLOv5 Hub")
                except Exception as e2:
                    try:
                        # Attempt 3: TorchScript JIT
                        model = torch.jit.load(path)
                        model.eval()
                        loaded_models[path] = model
                        model_errors.pop(path, None)
                        print(f"Successfully loaded {file} using JIT")
                    except Exception as e3:
                        model_errors[path] = f"Load failed: {str(e3)}"
                        print(f"Failed to load {file} after all attempts.")

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

    # 2. Download Custom Models from ENV
    if CUSTOM_MODEL_URLS:
        url_list = [u.strip() for u in CUSTOM_MODEL_URLS.split(';') if u.strip()]
        for url in url_list:
            download_model(url, overwrite=True)

    # 3. Load all models into memory
    load_all_models()
    print("Startup model check and load complete.")

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

def run_ensemble_inference(img: Image.Image):
    """Runs the image through ALL loaded models and returns aggregated findings."""
    final_weapons = []
    max_violence_prob = 0.0
    
    for path, model in loaded_models.items():
        fname = os.path.basename(path)
        # 1. Detect Weapons if it's a YOLO-style model
        if hasattr(model, 'names'): 
            try:
                results = model(img)
                for *box, conf, cls in results.xyxy[0]:
                    label = model.names[int(cls)]
                    # Common labels for violence/weapon detection
                    if label in ["knife", "scissors", "gun", "pistol", "firearm", "weapon", "punch", "kick"]:
                        final_weapons.append({
                            "type": label,
                            "confidence": round(float(conf), 4),
                            "box": [round(float(x), 2) for x in box],
                            "source_model": fname
                        })
            except Exception as e:
                print(f"Error running detector {fname}: {e}")
        
        # 2. Detect Violence if it's a classification-style model
        else:
            try:
                tensor = preprocess_for_violence(img)
                with torch.no_grad():
                    out = model(tensor)
                    # Support both [1] and [1, 1] output shapes
                    prob = torch.sigmoid(out).min().item() 
                    max_violence_prob = max(max_violence_prob, prob)
            except Exception as e:
                # Some models might fail if they expect different input shapes
                print(f"Error running classifier {fname}: {e}")
                
    return final_weapons, max_violence_prob

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
    """Lists files in the models directory with sizes and errors."""
    if not os.path.exists(MODEL_DIR):
        return {"error": "Models directory not found", "path": os.path.abspath(MODEL_DIR)}
        
    local_files = []
    for f in os.listdir(MODEL_DIR):
        path = os.path.join(MODEL_DIR, f)
        size_mb = round(os.path.getsize(path) / (1024 * 1024), 2)
        local_files.append({"name": f, "size_mb": size_mb})

    return {
        "local_models": local_files,
        "active_models": [os.path.basename(p) for p in loaded_models.keys()],
        "errors": {os.path.basename(p): err for p, err in model_errors.items()},
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
    load_all_models() # Sync memory
    return {"status": "completed", "results": results}

@app.post("/add-model")
async def add_model(request: AddModelRequest, token: str = Depends(verify_auth)):
    """Downloads a new model from a URL and loads it into the ensemble."""
    # 1. Pre-check size if Content-Length is available
    try:
        head = requests.head(request.url, allow_redirects=True)
        if int(head.headers.get('Content-Length', 0)) > MAX_MODEL_SIZE:
            raise HTTPException(status_code=400, detail="Model file exceeds 500MB limit.")
    except Exception:
        pass # Better to try download if HEAD fails
    
    # 2. Enforce MAX_MODELS limit (excluding defaults)
    files = [f for f in os.listdir(MODEL_DIR) if f.endswith('.pt')]
    if len(files) >= MAX_MODELS:
        defaults = get_default_filenames()
        # Find erasable models (non-defaults)
        erasable = [f for f in files if f not in defaults]
        if erasable:
            # Delete the oldest one
            erasable.sort(key=lambda x: os.path.getctime(os.path.join(MODEL_DIR, x)))
            os.remove(os.path.join(MODEL_DIR, erasable[0]))
            print(f"Deleted old model {erasable[0]} to stay within {MAX_MODELS} limit.")

    path = download_model(request.url, overwrite=request.overwrite)
    if not path:
        raise HTTPException(status_code=400, detail="Failed to download model")
    
    load_all_models() # Sync memory
    return {
        "status": "success",
        "model": os.path.basename(path),
        "total_active_models": len(loaded_models)
    }


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
            img = Image.open(io.BytesIO(contents))
            
            # Use the new Ensemble Inference
            weapons, violence_prob = run_ensemble_inference(img)
            
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
                "alert": alert,
                "models_used": list(loaded_models.keys())
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
