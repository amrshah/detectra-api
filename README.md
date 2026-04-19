# Detectra API 

Detectra API is a high-performance, lightweight backend service designed for real-time violence detection. Built specifically for resource-constrained environments (like Oracle A1Flex VPS), it provides robust endpoints for analyzing image feeds from CCTV cameras or mobile applications to identify weapons and violent activities.

## Key Features

- **Single Frame Detection**: High-speed inference for individual images.
- **Batch Processing**: Support for temporal smoothing through multi-frame analysis.
- **Multi-Concept Recognition**: 
    - **Weapons**: Detection of guns, pistols, and knives.
    - **Violent Activities**: Identification of physical fights and hitting.
    - **Critical Events**: Detection of shooting incidents.
- **Resource Optimized**: Optimized for CPU-only inference on ARM/x86 architectures.
- **Production Ready**: Fully dockerized with integrated authentication and rate limiting.

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Machine Learning**: [PyTorch](https://pytorch.org/), [MobileNetV2](https://pytorch.org/hub/pytorch_vision_mobilenet_v2/), [YOLOv5](https://github.com/ultralytics/yolov5)
- **Deployment**: Docker, Docker Compose, Portainer
- **Networking**: Cloudflare Tunnels (Zero Trust)

## Project Structure

```text
detectra-api/
├── app/
│   ├── main.py          # FastAPI application logic
│   ├── models/          # Pre-trained model checkpoints (.pt / .onnx)
│   └── requirements.txt  # Python dependencies
├── planning/            # Architectural and design documentation
├── .env                 # Environment variables (Internal)
├── .env.example         # Template for environment variables
├── Dockerfile           # Multi-stage production build
└── docker-compose.yml   # Stack orchestration
```

---

## Setup & Installation

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.10+ (for local development)

### 2. Configuration
Clone the `.env.example` to `.env` and update the values:
```bash
cp .env.example .env
```
Key variables:
- `AUTH_KEY`: Your secret API key for authorization.
- `MOCK_MODE`: Set to `true` to test API flow without loading heavy models.

### 3. Local Development
```bash
cd app
pip install -r requirements.txt
uvicorn main:app --reload --port 4141
```

---

## Deployment Instructions

### Docker Deployment
To run the API in a containerized environment:
```bash
docker-compose up -d --build
```

### Portainer Stack (Recommended)
1. Open your **Portainer** dashboard.
2. Go to **Stacks** > **Add stack**.
3. Copy the contents of `docker-compose.yml` into the web editor.
4. Add the environment variables from `.env` in the "Environment variables" section.
5. Click **Deploy the stack**.

### Cloudflare Tunnel Setup
To expose your API securely without opening ports:
1. Initialize a tunnel: `cloudflared tunnel create detectra-api`
2. Create a configuration mapping your domain to the container:
   ```yaml
    ingress:
      - hostname: api.yourdomain.com
        service: http://violence-api:4141
   ```
3. Route the traffic through the Zero Trust dashboard.

---

## API Documentation

The API includes built-in interactive documentation:
- **Swagger UI**: [https://api.yourdomain.com/docs](https://api.yourdomain.com/docs) (Interactive testing)
- **ReDoc**: [https://api.yourdomain.com/redoc](https://api.yourdomain.com/redoc) (Detailed documentation)

### Authentication
The API uses **Bearer Token** authentication. Include the following header in your requests:
`Authorization: Bearer <YOUR_AUTH_KEY>`

### Endpoints

#### Health Check
`GET /health`
- **Description**: Returns the operational status of the service and models.
- **Auth**: Public

#### Batch Detection
`POST /detect-batch`
- **Description**: Analyzes a batch of images for violence and weapons. Recommended for CCTV temporal smoothing.
- **Auth**: Bearer Token
- **Body**: `multipart/form-data` with multiple `images` files.
- **Logic**: Returns aggregated results using majority voting. Instructed to trigger alerts if a majority of frames are positive.

---

## Performance on Oracle VPS (A1 Flex)
- **Cold Start**: ~3s
- **Inference Latency**: 200ms - 500ms
- **Max Throughput**: ~2-3 concurrent requests (optimized for 1 worker)

## License
This project is developed for educational purposes only.
