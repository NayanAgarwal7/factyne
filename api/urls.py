from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('content/', views.submit_content, name='submit_content'),
]
