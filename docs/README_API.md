# Factyne Enterprise API

Real-time fact-checking API for newsrooms, publishers, and fact-checkers.

## Quick Start (2 minutes)

### 1. Get Your API Key
In Django shell
python manage.py shell
from django.contrib.auth.models import User
from core.models import APIKey
user = User.objects.first()
api_key = APIKey.objects.create(user=user, name="My Key")
print(f"Key: {api_key.key}")


### 2. Test the API
curl -X POST http://localhost:8000/api/v1/fact-check/
-H "Authorization: ApiKey YOUR_KEY"
-H "Content-Type: application/json"
-d '{"text": "The Earth is flat according to some scientists.", "async": false}'


### 3. Parse the Response
{
"claims": [
{"claim_text": "...", "confidence": 0.65}
],
"overall_trust_score": 0.65
}


## Use Cases

### 🗞️ Newsrooms
Auto-check articles before publishing:
response = requests.post(
'http://localhost:8000/api/v1/fact-check/',
headers={'Authorization': f'ApiKey {KEY}'},
json={'text': article_text}
)
if response.json()['overall_trust_score'] < 0.6:
print("⚠️ Low trust score - review needed!")


### ✅ Fact-Checkers
Batch process claims:
for claim in $(cat claims.txt); do
curl -X POST http://localhost:8000/api/v1/fact-check/
-H "Authorization: ApiKey $KEY"
-d "{"text": "$claim"}"
done


### 🛡️ Platforms
Moderate user content in real-time:
@app.route('/post', methods=['POST'])
def create_post():
text = request.json['text']
fact_check = requests.post(
'http://localhost:8000/api/v1/fact-check/',
headers={'Authorization': f'ApiKey {KEY}'},
json={'text': text}
).json()


if fact_check['overall_trust_score'] < 0.5:
    return {'error': 'Content flagged as low trust'}, 400

return {'id': save_post(text)}



---

## Features

✅ Real-time claim extraction  
✅ Confidence scoring  
✅ Negation detection  
✅ Contradiction detection  
✅ Rate limiting  
✅ User isolation  

---

## Pricing (Coming Soon)

| Tier | Price | Requests/Month |
|------|-------|----------------|
| Free | $0 | 1,000 |
| Starter | $99 | 25,000 |
| Pro | $499 | 250,000 |
| Enterprise | Custom | Unlimited |

---

## Support

- Docs: https://factyne.com/docs
- GitHub: https://github.com/factyne/factyne
- Email: support@factyne.com
