from django.db import models
from django.contrib.auth.models import User

class Content(models.Model):
    """Model for storing content to be fact-checked"""
    url = models.URLField(blank=True, null=True)
    raw_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    trust_score = models.FloatField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return f"Content ({self.id}) - Trust Score: {self.trust_score}"
    
    class Meta:
        ordering = ['-created_at']


class Claim(models.Model):
    """Model for storing extracted claims"""
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='claims')
    claim_text = models.TextField()
    confidence = models.FloatField(default=0.5)
    source = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Claim: {self.claim_text[:50]}..."
    
    class Meta:
        ordering = ['-confidence']


class Contradiction(models.Model):
    """Model for storing detected contradictions"""
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='contradictions')
    claim_a = models.CharField(max_length=255)
    claim_b = models.CharField(max_length=255)
    importance_score = models.FloatField(default=0.5)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Contradiction: {self.claim_a} vs {self.claim_b}"
    
    class Meta:
        ordering = ['-importance_score']


class Source(models.Model):
    """Model for storing source reliability scores"""
    name = models.CharField(max_length=255, unique=True)
    url = models.URLField(unique=True)
    reliability_score = models.FloatField(default=0.5)
    bias_score = models.FloatField(default=0.5)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} (Reliability: {self.reliability_score})"
    
    class Meta:
        ordering = ['-reliability_score']
