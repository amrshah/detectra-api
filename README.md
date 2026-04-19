# Detectra API 

Detectra API is a high-performance, lightweight backend service designed for real-time violence detection. Optimized for YOLOv8 and heuristic activity inference, it provides robust endpoints for analyzing image feeds while remaining highly efficient on CPU-bound hardware like Oracle A1 Flex and AMD Ryzen.

## Table of Contents
1. [Key Features](#key-features)
2. [Tech Stack](#tech-stack)
3. [System Requirements](#system-requirements)
4. [Project Structure](#project-structure)
5. [Setup & Installation](#setup--installation)
6. [Deployment Instructions](#deployment-instructions)
7. [API Documentation](#api-documentation)
    - [Authentication](#authentication)
    - [Response Specification](#response-specification)
8. [Integration Guide & WebP](#integration-guide--webp)
9. [Performance](#performance)
10. [License](#license)

## Key Features

- **YOLOv8 Engine (Object Detection)**: Detects weapons such as guns, pistols, and knives.
- **Heuristic Activity Inference**: Violent activities (e.g., fights, hitting) are inferred using multi-frame analysis and rule-based aggregation over detection outputs.
- **WebP Native Support**: Fully supports WebP format, allowing for high-quality analysis with up to 80% lower bandwidth consumption compared to JPEG/PNG.
- **Batch Processing**: Support for temporal smoothing through multi-frame analysis.
- **Multi-Concept Recognition**: 
    - **Weapons**: Detection of guns, pistols, and knives.
    - **Violent Activity Signals**: Approximated through temporal patterns (e.g., repeated detections, proximity, motion cues across frames).
- **Resource Optimized**: Specifically tuned for CPU-only inference on ARM/x86 (including AMD Ryzen) architectures.

## Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Machine Learning**: [PyTorch](https://pytorch.org/), [Ultralytics (YOLOv8)](https://github.com/ultralytics/ultralytics)
- **Deployment**: Docker, Docker Compose, Portainer

## System Requirements

### Minimum Requirements
- **CPU**: ARM64 (Oracle A1 Flex) or x86 (Intel/AMD) with 2+ cores.
- **RAM**: 4GB (for Real Inference).
- **Disk**: 2GB free space.

### Recommended (High Throughput)
- **CPU**: AMD Ryzen 5+ / Intel Core i5+
- **RAM**: 8GB+ 

---

## API Documentation

### Authentication
The API uses **Bearer Token** authentication. Include the following header in your requests:
`Authorization: Bearer <YOUR_AUTH_KEY>`

### Response Specification

#### Detection Output (`/detect-batch`)
The API returns a consolidated report for each frame in the batch plus an aggregated summary.

```json
{
  "results": [
    {
      "filename": "frame_001.webp",
      "weapons": [
        {
          "type": "pistol",
          "confidence": 0.8921,
          "box": [10.2, 50.1, 40.5, 90.2],
          "source_model": "yolov8n-weapon.pt"
        }
      ],
      "violence": {
        "detected": true,
        "confidence": 0.7542
      },
      "alert": true
    }
  ],
  "aggregated": {
    "alert": true,
    "total_alerts": 1,
    "method": "majority_vote"
  }
}
```

#### Management Output (`/models`)
Provides the current state of the model directory and loaded weights.

```json
{
  "local_models": [{"name": "weapon.pt", "size_mb": 6.25}],
  "active_models": [{"name": "weapon.pt", "labels": ["gun", "knife"]}],
  "errors": {}
}
```

---

## Integration Guide & WebP
For developers building client apps, please refer to the [Integration Guide](integration-guide.md). 

---

## Performance
- **Cold Start**: ~3s
- **Inference Latency (CPU)**: 
    - Single Frame: ~200ms – 600ms
    - Batch Mode: Improved throughput via parallel tensor inference
- **Max Throughput**: Scalable via Docker workers (Standard: 2-3 concurrent requests per worker).

## License
This project is developed for educational purposes only and you're allowed to adapt to your specific need/requirements.
