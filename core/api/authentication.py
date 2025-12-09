from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from core.models import APIKey


class APIKeyAuthentication(TokenAuthentication):
    """
    Custom authentication using APIKey model.
    Header format: Authorization: ApiKey <key_value>
    """
    keyword = 'ApiKey'

    def authenticate(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION', '').split()
        
        if len(auth) != 2 or auth[0].lower() != 'apikey':
            return None
        
        key = auth[1]
        
        try:
            api_key = APIKey.objects.get(key=key, is_active=True)
            return (api_key.user, None)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed('Invalid or inactive API key')
