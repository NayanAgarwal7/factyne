from rest_framework import serializers
from core.models import Content, Claim, Contradiction, Source


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ['id', 'name', 'reliability_score', 'bias_score']


class ClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Claim
        fields = ['id', 'claim_text', 'confidence', 'is_negated', 'has_qualifier', 'created_at']


class ContradictionSerializer(serializers.ModelSerializer):
    claim_a_text = serializers.CharField(source='claim_a.claim_text', read_only=True)
    claim_b_text = serializers.CharField(source='claim_b.claim_text', read_only=True)
    
    class Meta:
        model = Contradiction
        fields = [
            'id',
            'claim_a',
            'claim_a_text',
            'claim_b',
            'claim_b_text',
            'contradiction_type',
            'importance_score',
            'description',
            'created_at',
        ]


class ContentSerializer(serializers.ModelSerializer):
    claims = ClaimSerializer(many=True, read_only=True)
    
    class Meta:
        model = Content
        fields = [
            'id',
            'url',
            'raw_text',
            'user',
            'trust_score',
            'contradiction_count',
            'created_at',
            'claims',
        ]
