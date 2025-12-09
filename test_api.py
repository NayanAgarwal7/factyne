import requests

API_KEY = "a6W22eOVfb2Oljy9xOexhUuUzmHhjBDkDQO9piOBgiZ7s02QFE2Nqd4JmJnHCPYI"
BASE_URL = "http://localhost:8000"

headers = {
    "Authorization": f"ApiKey {API_KEY}",
    "Content-Type": "application/json"
}

# Test 1: Fact-check endpoint
print("🧪 Test 1: Fact-check API")
response = requests.post(
    f"{BASE_URL}/api/v1/fact-check/",
    headers=headers,
    json={
        "text": "The Earth is flat according to some scientists. Studies show climate change is real.",
        "async": False
    }
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
print()

# Test 2: Status endpoint (use correct ID format)
if response.status_code == 200:
    content_id = response.json()['id']
    print(f"🧪 Test 2: Status API (ID: {content_id})")
    status_response = requests.get(
        f"{BASE_URL}/api/v1/status/{content_id}/",
        headers=headers
    )
    print(f"Status Code: {status_response.status_code}")
    if status_response.status_code == 200:
        print(f"Response: {status_response.json()}")
    else:
        print(f"Error: {status_response.text}")
    print()

# Test 3: API Key Info
print("🧪 Test 3: API Key Info")
key_info_response = requests.get(
    f"{BASE_URL}/api/v1/key-info/",
    headers=headers
)
print(f"Status Code: {key_info_response.status_code}")
print(f"Response: {key_info_response.json()}")
