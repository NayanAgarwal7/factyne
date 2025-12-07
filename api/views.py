from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from core.models import Content
from .serializers import ContentSerializer
import random

@api_view(['GET'])
def health_check(request):
    """Simple health check endpoint"""
    return Response({
        'status': 'healthy',
        'message': 'Factyne API is running!'
    })

@api_view(['POST'])
def submit_content(request):
    """Submit content for fact-checking"""
    serializer = ContentSerializer(data=request.data)
    if serializer.is_valid():
        # Save the content
        content = serializer.save()
        
        # Generate a dummy trust score (0.0 - 1.0)
        # In future, this will call AI models
        trust_score = round(random.uniform(0.5, 0.95), 2)
        content.trust_score = trust_score
        content.save()
        
        # Return response with the score
        return Response({
            'id': content.id,
            'raw_text': content.raw_text[:100] + '...',
            'trust_score': content.trust_score,
            'status': 'Content received and scored',
            'message': 'Send content with raw_text field (required). Example: {"raw_text": "Your text here"}'
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'error': serializer.errors,
        'message': 'Invalid data. Send JSON with raw_text field.'
    }, status=status.HTTP_400_BAD_REQUEST)
