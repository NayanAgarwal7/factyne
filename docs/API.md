# Factyne API Documentation

## Quick Start

### Get API Key
1. Go to http://localhost:8000/admin/
2. Login with admin account
3. Click "API Keys" → "Add API Key"
4. Fill in name, click Save
5. Copy the generated key

### Make a Request

curl -X POST http://localhost:8000/api/v1/fact-check/
-H "Authorization: ApiKey YOUR_KEY_HERE"
-H "Content-Type: application/json"
-d '{"text": "The Earth is flat according to some scientists.", "async": false}'

### Response

{
"id": "12",
"status": "completed",
"claims": [
{
"claim_text": "The Earth is flat according to some scientists",
"confidence": 0.65
}
],
"overall_trust_score": 0.65,
"processing_time_ms": 18
}


---

## API Endpoints

### 1. POST /api/v1/fact-check/

Extract claims from text.

**Request:**

{
"text": "Article or claim text (required, max 50,000 chars)",
"url": "https://source-url.com (optional)",
"async": false
}


**Response (200 OK):**

{
"id": "12",
"status": "completed",
"claims": [
{
"id": 49,
"claim_text": "The Earth is flat according to some scientists",
"confidence": 0.65,
"is_negated": false,
"has_qualifier": false,
"created_at": "2025-12-09T07:33:28.130862Z"
}
],
"contradictions": 0,
"overall_trust_score": 0.65,
"processing_time_ms": 18
}


---

### 2. GET /api/v1/status/{id}/

Get results of a fact-check.

**Request:**

GET /api/v1/status/12/
Authorization: ApiKey YOUR_KEY_HERE


**Response (200 OK):**

{
"id": "12",
"status": "completed",
"claims": [
{
"id": 49,
"claim_text": "The Earth is flat according to some scientists",
"confidence": 0.65,
"is_negated": false,
"has_qualifier": false,
"created_at": "2025-12-09T07:33:28.130862Z"
}
],
"trust_score": 0.65,
"contradiction_count": 0,
"created_at": "2025-12-09T07:33:28.109542+00:00",
"updated_at": "2025-12-09T07:33:28.109542+00:00"
}


---

### 3. GET /api/v1/key-info/

Check your API key usage.

**Request:**

GET /api/v1/key-info/
Authorization: ApiKey YOUR_KEY_HERE


**Response (200 OK):**
{
"key_name": "Test Key",
"rate_limit": 1000,
"calls_this_month": 45,
"remaining": 955,
"is_active": true,
"created_at": "2025-12-09T07:11:17.267227+00:00",
"last_used": "2025-12-09T12:58:30.123456+00:00"
}



---

## Code Examples

### Python
import requests

API_KEY = "YOUR_API_KEY"
response = requests.post(
'http://localhost:8000/api/v1/fact-check/',
headers={'Authorization': f'ApiKey {API_KEY}'},
json={'text': 'Article text here', 'async': False}
)

data = response.json()
print(f"Trust Score: {data['overall_trust_score']}")
for claim in data['claims']:
print(f"- {claim['claim_text']} ({claim['confidence']})")


### JavaScript
const response = await fetch('http://localhost:8000/api/v1/fact-check/', {
method: 'POST',
headers: {
'Authorization': 'ApiKey YOUR_API_KEY',
'Content-Type': 'application/json'
},
body: JSON.stringify({
text: 'Article text here',
async: false
})
});

const data = await response.json();
console.log('Trust score:', data.overall_trust_score);



---

## Support
- GitHub: https://github.com/factyne/factyne
- Email: support@factyne.com


