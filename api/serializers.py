from rest_framework import serializers
from core.models import Content, Claim, Contradiction, Source

class ClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Claim
        fields = ['id', 'claim_text', 'confidence', 'source']

class ContentSerializer(serializers.ModelSerializer):
    claims = ClaimSerializer(many=True, read_only=True)
    
    class Meta:
        model = Content
        fields = ['id', 'url', 'raw_text', 'trust_score', 'created_at', 'claims']

class ContradictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contradiction
        fields = ['id', 'claim_a', 'claim_b', 'importance_score', 'description']

class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ['id', 'name', 'url', 'reliability_score', 'bias_score']
