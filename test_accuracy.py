import requests

API_KEY = "a6W22eOVfb2Oljy9xOexhUuUzmHhjBDkDQO9piOBgiZ7s02QFE2Nqd4JmJnHCPYI"
BASE_URL = "http://localhost:8000"

headers = {
    "Authorization": f"ApiKey {API_KEY}",
    "Content-Type": "application/json"
}

# Test cases with expected claims
test_cases = [
    {
        "name": "COVID Vaccine",
        "text": "Studies show COVID-19 vaccines are 95% effective at preventing severe disease. However, some people claim vaccines cause autism, which has been disproven by research.",
        "expected_claims": 3
    },
    {
        "name": "Climate Change",
        "text": "Global temperatures have risen by 1.1°C since pre-industrial times. Some scientists say this is natural variation, but climate data shows human activity is the primary cause.",
        "expected_claims": 3
    },
    {
        "name": "Flat Earth",
        "text": "The Earth is flat according to flat-earthers. NASA's satellite images prove the Earth is spherical. This contradiction has been definitively settled by science.",
        "expected_claims": 3
    },
    {
        "name": "Stock Market",
        "text": "Apple stock increased 50% last year. However, some analysts report it decreased in Q4. The overall trend shows growth despite quarterly fluctuations.",
        "expected_claims": 3
    }
]

print("🧪 ACCURACY TEST SUITE\n" + "="*60)

for test in test_cases:
    print(f"\n📌 Test: {test['name']}")
    print(f"Text: {test['text'][:70]}...")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/fact-check/",
        headers=headers,
        json={"text": test['text'], "async": False}
    )
    
    data = response.json()
    
    print(f"✅ Status: {response.status_code}")
    print(f"📊 Claims extracted: {len(data['claims'])} (expected ~{test['expected_claims']})")
    print(f"⚖️  Contradictions: {data['contradictions']}")
    print(f"💯 Trust score: {data['overall_trust_score']}")
    
    # Show each claim
    for i, claim in enumerate(data['claims'], 1):
        print(f"   {i}. {claim['claim_text'][:60]}... (confidence: {claim['confidence']})")

print("\n" + "="*60)
print("✅ Test suite complete!")
