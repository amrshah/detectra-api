# Detectra API 

Detectra API is a high-performance, lightweight backend service designed for real-time violence detection. Optimized for YOLOv8, it provides robust endpoints for analyzing image feeds to identify weapons and violent activities while remaining highly efficient on CPU-bound hardware.

## Table of Contents
1. [Key Features](#key-features)
2. [Tech Stack](#tech-stack)
3. [System Requirements](#system-requirements)
4. [Project Structure](#project-structure)
5. [Setup & Installation](#setup--installation)
6. [Deployment Instructions](#deployment-instructions)
7. [API Documentation](#api-documentation)
8. [Integration Guide & WebP](#integration-guide--webp)
9. [Performance](#performance)
10. [License](#license)

## Key Features

- **YOLOv8 Engine**: Utilizes the industry-leading YOLOv8 architecture for superior detection accuracy.
- **WebP Native Support**: Fully supports WebP format, allowing for high-quality analysis with up to 80% lower bandwidth consumption compared to JPEG/PNG.
- **Batch Processing**: Support for temporal smoothing through multi-frame analysis.
- **Multi-Concept Recognition**: 
    - **Weapons**: Detection of guns, pistols, and knives.
    - **Violent Activities**: Identification of physical fights and hitting.
- **Resource Optimized**: Specifically tuned for CPU-only inference on ARM/x86 (including AMD Ryzen) architectures.

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Machine Learning**: [PyTorch](https://pytorch.org/), [Ultralytics (YOLOv8)](https://github.com/ultralytics/ultralytics)
- **Deployment**: Docker, Docker Compose, Portainer
- **Networking**: Cloudflare Tunnels (Zero Trust)

## System Requirements

### Minimum Requirements
- **CPU**: ARM64 (Oracle A1 Flex) or x86 (Intel/AMD) with 2+ cores.
- **RAM**: 2GB (for Mock Mode) / 4GB (for Real Inference).
- **Disk**: 2GB free space.
- **Environment**: Docker 20.10+ and Docker Compose.

### Recommended (High Throughput)
- **CPU**: AMD Ryzen 5+ / Intel Core i5+
- **RAM**: 8GB+ 
- **OS**: Linux (Ubuntu 22.04 LTS recommended) or any Docker-capable host.

## Project Structure

```text
detectra-api/
├── app/
│   ├── main.py          # FastAPI application logic
│   ├── models/          # Pre-trained YOLOv8/TorchScript weights
│   └── requirements.txt  # Python dependencies
├── integration-guide.md # Multi-language developer documentation
├── Dockerfile           # Multi-stage production build
└── docker-compose.yml   # Stack orchestration
```

---

## Deployment Instructions

### Docker Deployment
The API is optimized for containerized environments. To deploy:
```bash
docker-compose up -d --build
```

### Portainer Stack
The stack configuration is designed for the ARM-based Oracle VPS but performs excellently on **AMD Ryzen** systems with ample RAM allocation in Docker. Ensure the `AUTH_KEY` is set to a secure string before deployment.

---

## API Documentation

The API includes built-in interactive documentation:
- **Swagger UI**: [https://api.yourdomain.com/docs](https://api.yourdomain.com/docs)
- **ReDoc**: [https://api.yourdomain.com/redoc](https://api.yourdomain.com/redoc)

---

## Integration Guide & WebP
For developers building client apps, please refer to the [Integration Guide](integration-guide.md). 

**WebP Recommendation:** Using **WebP** images for the `detect-batch` endpoint is highly recommended to ensure smooth performance on mobile networks and lower VPS ingress bandwidth.

---

## Performance
- **Cold Start**: ~3s
- **Inference Latency (Ryzen/A1 Flex)**: 150ms - 400ms per frame.
- **Max Throughput**: Scalable via Docker workers (Standard: 2-3 concurrent requests per worker).

## License
This project is developed for educational purposes only and you're allowed to adapt to your specific need/requirements.
