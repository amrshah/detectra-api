# Detectra API Integration Guide

This guide provides technical documentation for developers integrating the Detectra AI detection services into their applications.

## Base URL
All API requests should be made to the following base URL:
`https://detectra-api.alamiaai.com`

## Authentication
The API uses Bearer Token authentication. All requests to detection endpoints must include the following header:

```http
Authorization: Bearer <YOUR_AUTH_KEY>
```

## System Health
Before initiating batch processing, it is recommended to verify the API status.

### GET /health
Checks the current operational status of the API and its models.

**Response Body:**
```json
{
  "status": "healthy",
  "mock_mode": false,
  "models_status": {
    "directory_exists": true,
    "files": ["model1.pt", "model2.pt"]
  }
}
```

---

## Detection Endpoints

### POST /detect-batch
Processes a batch of images for violence and weapon detection. This endpoint supports multiple images in a single request and uses an ensemble of all active models to verify results.

**Request Type:** `multipart/form-data`

**Parameters:**
- `images`: A list of image files. (Maximum 10 images per request).

**Response Structure:**
The API returns a JSON object containing a `results` array and an `aggregated` summary.

```json
{
  "results": [
    {
      "filename": "frame1.jpg",
      "weapons": [
        {
          "type": "pistol",
          "confidence": 0.8542,
          "box": [10.5, 20.1, 50.2, 80.5],
          "source_model": "weapon_detector_v8.pt"
        }
      ],
      "violence": {
        "detected": true,
        "confidence": 0.8542
      },
      "critical_event": {
        "shooting": false
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

#### Fields Description:
- **weapons**: A list of detected objects (knife, pistol, rifle, etc.) with their bounding boxes and confidence scores.
- **violence**: Summarized violence detection status.
- **critical_event.shooting**: Flagged as true if a firearm and a high violence probability are detected simultaneously.
- **alert**: A boolean indicating if any threat was detected in that specific frame.
- **aggregated.alert**: The final decision for the entire batch.

## Error Handling
The API utilizes standard HTTP status codes:
- **200 OK**: Request processed successfully.
- **401 Unauthorized**: Missing or invalid Auth Key.
- **400 Bad Request**: Maximum image limit exceeded or invalid file format.
- **500 Internal Server Error**: Unexpected server failure.

## Implementation Example (Python/Requests)

```python
import requests

url = "https://detectra-api.alamiaai.com/detect-batch"
headers = {"Authorization": "Bearer YOUR_AUTH_KEY"}
files = [
    ("images", open("frame1.jpg", "rb")),
    ("images", open("frame2.jpg", "rb"))
]

response = requests.post(url, headers=headers, files=files)
print(response.json())
```

## Implementation Example (Dart / Flutter)

Using the `http` package:

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<void> detectViolence(List<String> imagePaths) async {
  var url = Uri.parse('https://detectra-api.alamiaai.com/detect-batch');
  var request = http.MultipartRequest('POST', url);
  
  // Add Headers
  request.headers.addAll({
    'Authorization': 'Bearer YOUR_AUTH_KEY',
  });

  // Add Files
  for (var path in imagePaths) {
    request.files.add(await http.MultipartFile.fromPath('images', path));
  }

  // Send Request
  var streamedResponse = await request.send();
  var response = await http.Response.fromStream(streamedResponse);

  if (response.statusCode == 200) {
    var data = jsonDecode(response.body);
    print('Detection Status: ${data['aggregated']['alert']}');
  } else {
    print('Request failed with status: ${response.statusCode}');
  }
}
```
