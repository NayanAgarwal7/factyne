"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from core.api.endpoints import fact_check_api, fact_check_status, api_key_info
from core.views import submit_page, dashboard, content_detail, content_pdf, api_docs


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Web UI
    path('', dashboard, name='dashboard'),
    path('submit/', submit_page, name='submit_page'),
    path('content/<int:content_id>/', content_detail, name='content_detail'),
    path('content/<int:content_id>/pdf/', content_pdf, name='content_pdf'),
    path('api-docs/', api_docs, name='api_docs'),
    
    # REST API v1
    path('api/v1/fact-check/', fact_check_api, name='fact_check_api'),
    path('api/v1/status/<int:content_id>/', fact_check_status, name='fact_check_status'),  # Changed from uuid to int
    path('api/v1/key-info/', api_key_info, name='api_key_info'),
]



