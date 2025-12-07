from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    
    # Content endpoints
    path('content/', views.submit_content, name='submit_content'),
    path('content/list/', views.content_list, name='content_list'),
    path('content/<int:pk>/', views.content_detail, name='content_detail'),
    path('content/<int:pk>/claims/', views.content_claims, name='content_claims'),
    
    # Claim endpoints
    path('claims/<int:pk>/', views.claim_detail, name='claim_detail'),
    
    # Contradiction endpoints
    path('contradictions/', views.contradictions_list, name='contradictions_list'),
]
