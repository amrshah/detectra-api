# Detectra API 

Detectra API is a high-performance, lightweight backend service designed for real-time violence detection. Built specifically for resource-constrained environments (like Oracle A1Flex VPS), it provides robust endpoints for analyzing image feeds from CCTV cameras or mobile applications to identify weapons and violent activities.

## Table of Contents
1. [Key Features](#key-features)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Setup & Installation](#setup--installation)
5. [Deployment Instructions](#deployment-instructions)
6. [API Documentation](#api-documentation)
    - [Authentication](#authentication)
    - [Core Endpoints](#core-endpoints)
    - [Management Endpoints](#management-endpoints)
7. [Integration Guide](#integration-guide)
8. [Performance](#performance-on-oracle-vps-a1-flex)
9. [License](#license)

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
- **Machine Learning**: [PyTorch](https://pytorch.org/), [Ultralytics (YOLOv8)](https://github.com/ultralytics/ultralytics)
- **Deployment**: Docker, Docker Compose, Portainer
- **Networking**: Cloudflare Tunnels (Zero Trust)

## Project Structure

```text
detectra-api/
├── app/
│   ├── main.py          # FastAPI application logic
│   ├── models/          # Pre-trained model checkpoints (.pt)
│   └── requirements.txt  # Python dependencies
├── planning/            # Architectural and design documentation
├── .env                 # Environment variables (Internal)
├── .env.example         # Template for environment variables
├── Dockerfile           # Multi-stage production build
├── docker-compose.yml   # Stack orchestration
└── integration-guide.md # Developer documentation
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
- `DEBUG_MODE`: Set to `true` to receive detailed detection metadata in responses.

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

---

## API Documentation

The API includes built-in interactive documentation:
- **Swagger UI**: [https://api.yourdomain.com/docs](https://api.yourdomain.com/docs)
- **ReDoc**: [https://api.yourdomain.com/redoc](https://api.yourdomain.com/redoc)

### Authentication
The API uses **Bearer Token** authentication. Include the following header in your requests:
`Authorization: Bearer <YOUR_AUTH_KEY>`

### Core Endpoints

#### GET /health
- **Description**: Returns the operational status of the service, active models, and mock mode status.
- **Auth**: Public

#### POST /detect-batch
- **Description**: Analyzes a batch of images for violence and weapons. 
- **Auth**: Bearer Token
- **Body**: `multipart/form-data` with `images` files.

### Management Endpoints

#### GET /models
- **Description**: Lists all local model files, their sizes, active status, and any loading errors.
- **Auth**: Bearer Token

#### POST /add-model
- **Description**: Downloads and live-loads a new model via URL. Enforces a 500MB size limit and a 6-model quota.
- **Auth**: Bearer Token

#### POST /download-default-models
- **Description**: Resets/redownloads all baseline AI models provided during initial setup.
- **Auth**: Bearer Token

---

## Integration Guide
For comprehensive developer documentation including code samples in Python, Dart/Flutter, PHP/Laravel, and Node.js, please refer to the [Integration Guide](integration-guide.md).

---

## Performance on Oracle VPS (A1 Flex)
- **Cold Start**: ~3s
- **Inference Latency**: 200ms - 500ms
- **Max Throughput**: ~2-3 concurrent requests (optimized for 1 worker)

## License
This project is developed for educational purposes only and you're allowed to adapt to your specific need/requirements.
