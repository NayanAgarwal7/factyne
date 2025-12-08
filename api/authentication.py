from rest_framework import authentication, exceptions
from core.models import APIKey
from django.utils import timezone


class APIKeyAuthentication(authentication.BaseAuthentication):
    """Custom authentication using API keys."""
    
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_API_KEY')
        
        if not api_key:
            return None
        
        try:
            key_obj = APIKey.objects.get(key=api_key, is_active=True)
            key_obj.last_used = timezone.now()
            key_obj.save(update_fields=['last_used'])
            
            return (key_obj.user, None)
            
        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')
