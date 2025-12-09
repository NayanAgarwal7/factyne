from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from core.models import Content, Claim, APIKey
from core.claim_extractor_api import extract_claims, detect_contradictions, calculate_trust_score
from api.serializers import ClaimSerializer
from core.tasks import process_content_async
import time


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def fact_check_api(request):
    """
    POST /api/v1/fact-check/
    
    Fact-check content and extract claims.
    """
    text = request.data.get('text', '').strip()
    url = request.data.get('url', '').strip() or None
    async_mode = request.data.get('async', False)
    
    if not text:
        return Response(
            {'error': 'Missing required field: text (must be non-empty)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(text) > 50000:
        return Response(
            {'error': 'Text exceeds 50,000 character limit'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    content = Content.objects.create(
        raw_text=text,
        url=url,
        user=request.user
    )
    
    start_time = time.time()
    
    if async_mode:
        process_content_async.delay(content.id)
        return Response({
            'id': str(content.id),
            'status': 'queued',
            'message': 'Processing started. Check /api/v1/status/{id}/ for results'
        }, status=status.HTTP_202_ACCEPTED)
    else:
        try:
            # Extract claims, detect contradictions, calculate trust score
            claims = extract_claims(text, content=content)
            contradictions = detect_contradictions(claims)
            trust_score = calculate_trust_score(claims, contradictions)
            
            # Update content with results
            content.trust_score = trust_score
            content.contradiction_count = len(contradictions)
            content.save(update_fields=['trust_score', 'contradiction_count'])
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return Response({
                'id': str(content.id),
                'status': 'completed',
                'claims': ClaimSerializer(claims, many=True).data,
                'contradictions': len(contradictions),
                'overall_trust_score': round(trust_score, 2),
                'processing_time_ms': processing_time
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': f'Processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fact_check_status(request, content_id):
    """GET /api/v1/status/{id}/"""
    try:
        content = Content.objects.get(id=content_id, user=request.user)
        claims = Claim.objects.filter(content=content)
        
        is_completed = claims.exists() or content.trust_score > 0.0
        
        return Response({
            'id': str(content.id),
            'status': 'completed' if is_completed else 'processing',
            'claims': ClaimSerializer(claims, many=True).data,
            'trust_score': round(content.trust_score, 2),
            'contradiction_count': content.contradiction_count,
            'created_at': content.created_at.isoformat(),
            'updated_at': content.updated_at.isoformat()
        }, status=status.HTTP_200_OK)
    
    except Content.DoesNotExist:
        return Response(
            {'error': f'Content {content_id} not found or not accessible'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error retrieving status: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_key_info(request):
    """GET /api/v1/key-info/"""
    try:
        api_key = APIKey.objects.get(user=request.user)
        
        return Response({
            'key_name': api_key.name,
            'rate_limit': api_key.rate_limit,
            'calls_this_month': api_key.calls_this_month,
            'remaining': max(0, api_key.rate_limit - api_key.calls_this_month),
            'is_active': api_key.is_active,
            'created_at': api_key.created_at.isoformat(),
            'last_used': api_key.last_used.isoformat() if api_key.last_used else None
        }, status=status.HTTP_200_OK)
    
    except APIKey.DoesNotExist:
        return Response(
            {'error': 'No API key associated with this user'},
            status=status.HTTP_404_NOT_FOUND
        )

