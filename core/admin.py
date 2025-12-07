from django.contrib import admin
from .models import Content, Claim, Contradiction, Source


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'trust_score')
    search_fields = ('raw_text',)
    list_filter = ('created_at', 'trust_score')


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('claim_text', 'confidence', 'content', 'created_at')
    search_fields = ('claim_text',)
    list_filter = ('confidence',)


@admin.register(Contradiction)
class ContradictionAdmin(admin.ModelAdmin):
    list_display = ('claim_a', 'claim_b', 'importance_score', 'created_at')
    search_fields = ('claim_a', 'claim_b')
    list_filter = ('importance_score',)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'reliability_score', 'bias_score', 'last_updated')
    search_fields = ('name',)
    list_filter = ('reliability_score',)
