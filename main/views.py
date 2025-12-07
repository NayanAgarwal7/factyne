from django.shortcuts import render
from django.http import JsonResponse

def index(request):
    """Landing page"""
    return JsonResponse({
        'name': 'Factyne',
        'tagline': 'Trust Instantly. Know More. Doubt Less.',
        'version': '0.1.0',
        'status': 'Development'
    })
