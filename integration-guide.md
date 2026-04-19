# Detectra API Integration Guide

This document provides technical specifications and implementation examples for integrating Detectra AI services into various software environments.

## Table of Contents
1. [Authentication](#authentication)
2. [Base URL](#base-url)
3. [System Health](#system-health)
4. [Detection Endpoints](#detection-endpoints)
5. [Inference Support & WebP](#inference-support--webp)
6. [Implementation Examples](#implementation-examples)
    - [Python](#python-example)
    - [Dart / Flutter](#dart--flutter-example)
    - [PHP / Laravel](#php--laravel-example)
    - [Node.js (Axios)](#nodejs-axios-example)
    - [React (JavaScript)](#react-javascript-example)
    - [Angular (TypeScript)](#angular-typescript-example)
    - [cURL](#curl-example)
7. [Error Handling](#error-handling)

## Authentication
The API utilizes Bearer Token authentication. All requests to detection and management endpoints must include the following header:

```http
Authorization: Bearer <YOUR_AUTH_KEY>
```

## Base URL
All requests should be directed to your deployed instance:
`https://api.yourdomain.com`

---

## Inference Support & WebP
The Detectra API utilizes **YOLOv8**, which provides native and efficient support for the **WebP** image format. 

**Integration Tip:** Developers are strongly encouraged to use **WebP** instead of standard JPEG or PNG. WebP offers significantly higher compression with better quality, reducing latency and bandwidth consumption during batch uploads to the VPS.

---

## System Health
It is recommended to implement a health check in your integration flow to ensure service availability.

### GET /health
Returns the operational status of the API and its underlying model directory.

---

## Implementation Examples

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

### Python Example
```python
import requests

url = "https://api.yourdomain.com/detect-batch"
headers = {"Authorization": "Bearer YOUR_AUTH_KEY"}
files = [("images", open("frame1.webp", "rb"))] # WebP recommended

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

### Dart / Flutter Example
```dart
import 'package:http/http.dart' as http;

Future<void> detectViolence(List<String> imagePaths) async {
  var url = Uri.parse('https://api.yourdomain.com/detect-batch');
  var request = http.MultipartRequest('POST', url);
  request.headers['Authorization'] = 'Bearer YOUR_AUTH_KEY';

  for (var path in imagePaths) {
    request.files.add(await http.MultipartFile.fromPath('images', path));
  }

  var response = await http.Response.fromStream(await request.send());
  print(response.body);
}
```

### PHP / Laravel Example
```php
use Illuminate\Support\Facades\Http;

$response = Http::withToken('YOUR_AUTH_KEY')
    ->attach('images', file_get_contents('frame1.webp'), 'frame1.webp')
    ->post('https://api.yourdomain.com/detect-batch');

return $response->json();
```

### Node.js (Axios) Example
```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const form = new FormData();
form.append('images', fs.createReadStream('frame1.webp'));

axios.post('https://api.yourdomain.com/detect-batch', form, {
    headers: {
        ...form.getHeaders(),
        'Authorization': 'Bearer YOUR_AUTH_KEY'
    }
}).then(res => console.log(res.data));
```

### cURL Example
```bash
curl -X POST "https://api.yourdomain.com/detect-batch" \
     -H "Authorization: Bearer YOUR_AUTH_KEY" \
     -F "images=@frame1.webp" 
```

## Error Handling
| Code | Meaning | Resolution |
|------|---------|------------|
| 200 | OK | Request succeeded. |
| 401 | Unauthorized | Verify Bearer token. |
| 400 | Bad Request | Check image counts or file formats. |
| 413 | Payload Too Large | Ensure individual files are within size limits. |
| 500 | Server Error | Internal failure, check server logs. |
