from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from core.models import Content, Claim
from .serializers import ContentSerializer

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
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
