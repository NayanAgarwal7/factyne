from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import models
from core.models import Content, Claim, Contradiction
from core.claim_extractor import ClaimExtractor, ContradictionDetector
from api.serializers import ContentSerializer, ClaimSerializer, ContradictionSerializer
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
def health_check(request):
    """Health check endpoint."""
    return Response({
        'status': 'healthy',
        'message': 'Factyne API is running!',
        'version': '0.1.0'
    })


@api_view(['POST'])
def submit_content(request):
    """
    Submit content for fact-checking.
    Automatically extracts claims and detects contradictions.
    """
    serializer = ContentSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'errors': serializer.errors,
            'message': 'Invalid data. Send JSON with raw_text field.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    content = serializer.save()
    
    # Extract claims from text
    extracted_claims = ClaimExtractor.extract_claims(content.raw_text)
    
    if not extracted_claims:
        # No claims found, set neutral trust score
        content.trust_score = 0.5
        content.save()
        return Response({
            'id': content.id,
            'message': 'Content saved, but no factual claims could be extracted.',
            'claims': [],
            'trust_score': content.trust_score,
        }, status=status.HTTP_201_CREATED)
    
    # Create Claim objects in database
    created_claims = []
    for extracted_claim in extracted_claims:
        claim = Claim.objects.create(
            content=content,
            claim_text=extracted_claim['claim_text'],
            confidence=extracted_claim['confidence'],
            is_negated=extracted_claim['is_negated'],
            has_qualifier=extracted_claim['has_qualifier'],
        )
        created_claims.append(claim)
    
    # Detect contradictions with existing claims from all content
    all_existing_claims = Claim.objects.exclude(content=content).values('id', 'claim_text', 'is_negated', 'content_id')
    
    for new_claim in created_claims:
        contradictions_found = ContradictionDetector.detect_contradictions_batch(
            new_claim.claim_text,
            list(all_existing_claims)
        )
        
        for contradiction_info in contradictions_found:
            # Find the existing claim object
            try:
                existing_claim = Claim.objects.get(claim_text=contradiction_info['existing_claim_text'])
                Contradiction.objects.update_or_create(
                    claim_a=new_claim,
                    claim_b=existing_claim,
                    defaults={
                        'importance_score': contradiction_info['importance_score'],
                        'contradiction_type': contradiction_info['type'],
                        'description': contradiction_info['explanation'],
                    }
                )
            except Claim.DoesNotExist:
                pass
    
    # Recalculate trust score
    content.calculate_trust_score()
    
    return Response({
        'id': content.id,
        'raw_text': content.raw_text[:100] + ('...' if len(content.raw_text) > 100 else ''),
        'claims_count': len(created_claims),
        'claims': ClaimSerializer(created_claims, many=True).data,
        'contradiction_count': content.contradiction_count,
        'trust_score': content.trust_score,
        'status': 'Content processed successfully',
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def content_detail(request, pk):
    """
    Get a specific content with all its claims and contradictions.
    """
    content = get_object_or_404(Content, pk=pk)
    
    claims = content.claims.all()
    contradictions = Contradiction.objects.filter(
        models.Q(claim_a__content=content) | models.Q(claim_b__content=content)
    )
    
    return Response({
        'id': content.id,
        'raw_text': content.raw_text,
        'user': content.user.username if content.user else None,
        'trust_score': content.trust_score,
        'created_at': content.created_at,
        'claims': ClaimSerializer(claims, many=True).data,
        'contradictions': ContradictionSerializer(contradictions, many=True).data,
        'summary': {
            'claims_extracted': claims.count(),
            'contradictions_found': contradictions.count(),
            'avg_claim_confidence': round(sum(c.confidence for c in claims) / claims.count(), 2) if claims.exists() else 0,
        }
    })


@api_view(['GET'])
def content_list(request):
    """List all content with pagination and filtering."""
    contents = Content.objects.all().order_by('-created_at')
    
    # Simple pagination
    limit = int(request.query_params.get('limit', 10))
    offset = int(request.query_params.get('offset', 0))
    
    paginated = contents[offset:offset+limit]
    
    return Response({
        'count': contents.count(),
        'offset': offset,
        'limit': limit,
        'results': [
            {
                'id': c.id,
                'trust_score': c.trust_score,
                'claims_count': c.claims.count(),
                'contradiction_count': c.contradiction_count,
                'created_at': c.created_at,
                'raw_text': c.raw_text[:100] + '...',
            }
            for c in paginated
        ]
    })


@api_view(['GET'])
def content_claims(request, pk):
    """Get all claims for a specific content."""
    content = get_object_or_404(Content, pk=pk)
    claims = content.claims.all()
    
    return Response({
        'content_id': content.id,
        'claims_count': claims.count(),
        'claims': ClaimSerializer(claims, many=True).data,
    })


@api_view(['GET'])
def contradictions_list(request):
    """List all detected contradictions."""
    contradictions = Contradiction.objects.all().order_by('-importance_score')
    
    # Filter by type
    contradiction_type = request.query_params.get('type', None)
    if contradiction_type:
        contradictions = contradictions.filter(contradiction_type=contradiction_type)
    
    limit = int(request.query_params.get('limit', 20))
    offset = int(request.query_params.get('offset', 0))
    
    paginated = contradictions[offset:offset+limit]
    
    return Response({
        'count': contradictions.count(),
        'offset': offset,
        'limit': limit,
        'types_available': ['direct_negation', 'semantic', 'statistical'],
        'results': ContradictionSerializer(paginated, many=True).data,
    })


@api_view(['GET'])
def claim_detail(request, pk):
    """Get a specific claim with its contradictions."""
    claim = get_object_or_404(Claim, pk=pk)
    
    contradictions_a = Contradiction.objects.filter(claim_a=claim)
    contradictions_b = Contradiction.objects.filter(claim_b=claim)
    
    return Response({
        'id': claim.id,
        'claim_text': claim.claim_text,
        'confidence': claim.confidence,
        'is_negated': claim.is_negated,
        'has_qualifier': claim.has_qualifier,
        'content_id': claim.content.id,
        'created_at': claim.created_at,
        'contradictions_count': contradictions_a.count() + contradictions_b.count(),
        'contradictions': ContradictionSerializer(
            list(contradictions_a) + list(contradictions_b),
            many=True
        ).data,
    })
