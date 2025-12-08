from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('submit/', views.submit, name='submit'),
    path('content/<int:content_id>/', views.content_detail, name='content_detail'),
    path('api/content/', views.api_content_list, name='api_content_list'),
    path('api/claims/<int:content_id>/', views.api_claims_for_content, name='api_claims'),
    path('api/contradictions/', views.api_contradictions, name='api_contradictions'),
]
