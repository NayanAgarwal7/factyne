from django.urls import path
from . import views
from core.export import ReportExporter
from django.http import HttpResponse

def export_pdf_view(request, content_id):
    return ReportExporter.export_pdf(content_id)

def export_json_view(request, content_id):
    return ReportExporter.export_json(content_id)

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
    path('content/<int:content_id>/export/pdf/', export_pdf_view, name='export_pdf'),
    path('content/<int:content_id>/export/json/', export_json_view, name='export_json'),
]
