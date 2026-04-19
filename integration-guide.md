# Detectra API Integration Guide

This document provides technical specifications and implementation examples for integrating Detectra AI services into various software environments.

## Table of Contents
1. [Authentication](#authentication)
2. [Base URL](#base-url)
3. [System Health](#system-health)
4. [Detection Strategies](#detection-strategies)
    - [Single Image Detection](#single-image-detection)
    - [Multi-Image (Batch) Detection](#multi-image-batch-detection)
    - [Temporal Smoothing](#temporal-smoothing)
5. [Inference Support & WebP](#inference-support--webp)
6. [Implementation Examples](#implementation-examples)
    - [Temporal Smoothing (Flutter/Dart)](#temporal-smoothing-flutterdart)
    - [React (JavaScript)](#react-javascript-example)
    - [Angular (TypeScript)](#angular-typescript-example)
    - [PHP / Laravel](#php--laravel-example)
    - [Python](#python-example)
    - [cURL](#curl-example)
7. [Error Handling](#error-handling)

## Authentication
The API utilizes Bearer Token authentication. All requests to detection and management endpoints must include the following header:

```http
Authorization: Bearer <YOUR_AUTH_KEY>
```

## Base URL
`https://api.yourdomain.com`

---

## Detection Strategies

### Single Image Detection
Use this for applications requiring the lowest possible latency for immediate feedback.
- **Workflow**: Capture frame -> Send to `/detect-batch` (with 1 image) -> Process result.
- **Pros**: Fastest response.
- **Cons**: higher risk of false positives due to lighting or motion blur in 

### Multi-Image (Batch) Detection
Standard for most surveillance applications. Processes several frames as a single context.
- **Workflow**: Buffer `n` frames -> Send to `/detect-batch`.
- **Logic**: The API scans all frames and identifies if a consistent threat is appearing across the sample.

### Temporal Smoothing
Temporal smoothing is the gold standard for reducing false alerts in AI video analysis. Instead of alerting on a single positive frame, you analyze a sequence of frames over a short window (e.g., 1-2 seconds).

**How it works:**
1.  Capture 5 to 10 frames at short intervals (e.g., every 200ms).
2.  Transmit these frames as a single batch to the `/detect-batch` endpoint.
3.  The API performs an aggregate check: if the system identifies a threat in more than 50% of the frames (majority vote), the `aggregated.alert` field will be marked `true`.

---

## Inference Support & WebP
Native support for **YOLOv8** and **WebP**. Developers are strongly urged to use the **WebP** format during temporal smoothing batches to keep the total payload size low and the upload speed high.

---

## Implementation Examples

### Temporal Smoothing (Flutter/Dart)
This example demonstrates how to maintain a rolling buffer of frames and dispatch a batch once the buffer is full.

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class TemporalDetectionService {
  final List<String> _frameBuffer = [];
  final int batchSize = 5;

  // Called every time a frame is captured by the camera
  Future<void> onFrameCaptured(String imagePath) async {
    _frameBuffer.add(imagePath);

    if (_frameBuffer.length >= batchSize) {
      // Buffer is full, dispatch for temporal analysis
      await _dispatchBatch(List.from(_frameBuffer));
      _frameBuffer.clear(); // Reset buffer
    }
  }

  Future<void> _dispatchBatch(List<String> paths) async {
    var url = Uri.parse('https://api.yourdomain.com/detect-batch');
    var request = http.MultipartRequest('POST', url);
    request.headers['Authorization'] = 'Bearer YOUR_AUTH_KEY';

    for (var path in paths) {
      request.files.add(await http.MultipartFile.fromPath('images', path));
    }

    var response = await http.Response.fromStream(await request.send());
    if (response.statusCode == 200) {
      var data = jsonDecode(response.body);
      if (data['aggregated']['alert'] == true) {
        // Trigger UI Alert: Violence confirmed over temporal window
        print('CRITICAL: Violence Detected!');
      }
    }
  }
}
```

### React (JavaScript) Example
```javascript
import axios from 'axios';

const detectImages = async (files) => {
  const formData = new FormData();
  files.forEach(file => formData.append('images', file));

  const response = await axios.post('https://api.yourdomain.com/detect-batch', formData, {
    headers: {
      'Authorization': 'Bearer YOUR_AUTH_KEY',
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
};
```

### Angular (TypeScript) Example
```typescript
import { HttpClient, HttpHeaders } from '@angular/common/http';

export class DetectionService {
  constructor(private http: HttpClient) {}

  detectBatch(files: File[]) {
    const formData = new FormData();
    files.forEach(file => formData.append('images', file));

    const headers = new HttpHeaders({
      'Authorization': 'Bearer YOUR_AUTH_KEY'
    });

    return this.http.post('https://api.yourdomain.com/detect-batch', formData, { headers });
  }
}
```

### Python Example (Batch Check)
```python
import requests

url = "https://api.yourdomain.com/detect-batch"
headers = {"Authorization": "Bearer YOUR_AUTH_KEY"}
files = [("images", open(f"frame_{i}.webp", "rb")) for i in range(5)]

response = requests.post(url, headers=headers, files=files)
print(f"Batch Alert Status: {response.json()['aggregated']['alert']}")
```

### cURL Example
```bash
curl -X POST "https://api.yourdomain.com/detect-batch" \
     -H "Authorization: Bearer YOUR_AUTH_KEY" \
     -F "images=@frame1.webp" \
     -F "images=@frame2.webp" \
     -F "images=@frame3.webp"
```

## Error Handling
| Code | Meaning | Resolution |
|------|---------|------------|
| 200 | OK | Request succeeded. |
| 401 | Unauthorized | Verify Bearer token. |
| 400 | Bad Request | Check image counts or file formats. |
| 500 | Server Error | Internal failure, check server logs. |
