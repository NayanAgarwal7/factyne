from django.contrib import admin
from django.utils.html import format_html
from core.models import Content, Claim, APIKey, Evidence, Contradiction, Source


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'key_preview', 'is_active', 'rate_limit', 'calls_this_month', 'created_at')
    readonly_fields = ('key', 'created_at', 'last_used')
    fields = ('user', 'name', 'key', 'is_active', 'rate_limit', 'calls_this_month', 'created_at', 'last_used')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'name')
    
    def key_preview(self, obj):
        """Show first 8 and last 4 chars of key"""
        return f"{obj.key[:8]}****{obj.key[-4:]}"
    key_preview.short_description = "API Key"

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'trust_score_display', 'claim_count', 'contradiction_count', 'created_at')
    list_filter = ('created_at', 'trust_score', 'contradiction_count')
    search_fields = ('raw_text',)
    readonly_fields = ('trust_score', 'contradiction_count', 'created_at', 'updated_at', 'claim_summary')
    fieldsets = (
        ('Content', {'fields': ('url', 'raw_text', 'user')}),
        ('Scoring', {'fields': ('trust_score', 'contradiction_count')}),
        ('Summary', {'fields': ('claim_summary',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def trust_score_display(self, obj):
        score = obj.trust_score or 0.0
        color = 'green' if score > 0.7 else 'orange' if score > 0.4 else 'red'
        # Use string formatting *before* passing into format_html
        formatted = "{:.2f}".format(score)
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            formatted,
        )
    trust_score_display.short_description = 'Trust Score'

    
    def claim_count(self, obj):
        return obj.claims.count()
    claim_count.short_description = 'Claims'
    
    def claim_summary(self, obj):
        claims = obj.claims.all()[:5]
        if not claims:
            return "No claims extracted yet."
        return "\n".join([f"• {c.claim_text[:70]}... (conf: {c.confidence})" for c in claims])
    claim_summary.short_description = 'Claims Summary'


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('claim_preview', 'confidence', 'is_negated', 'has_qualifier', 'content_link', 'created_at')
    list_filter = ('confidence', 'is_negated', 'has_qualifier', 'created_at')
    search_fields = ('claim_text',)
    readonly_fields = ('content', 'created_at')
    fieldsets = (
        ('Claim', {'fields': ('content', 'claim_text')}),
        ('Attributes', {'fields': ('confidence', 'is_negated', 'has_qualifier', 'source')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )
    
    def claim_preview(self, obj):
        return obj.claim_text[:80] + ("..." if len(obj.claim_text) > 80 else "")
    claim_preview.short_description = 'Claim'
    
    def content_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:core_content_change', args=[obj.content.id])
        return format_html('<a href="{}">{}</a>', url, f'Content #{obj.content.id}')
    content_link.short_description = 'Content'


@admin.register(Contradiction)
class ContradictionAdmin(admin.ModelAdmin):
    list_display = ('contradiction_type', 'importance_score_display', 'claim_a_preview', 'claim_b_preview', 'created_at')
    list_filter = ('contradiction_type', 'importance_score', 'created_at')
    search_fields = ('claim_a__claim_text', 'claim_b__claim_text', 'description')
    readonly_fields = ('claim_a', 'claim_b', 'created_at', 'description')
    fieldsets = (
        ('Claims', {'fields': ('claim_a', 'claim_b')}),
        ('Analysis', {'fields': ('contradiction_type', 'importance_score', 'description')}),
        ('Timestamps', {'fields': ('created_at',)}),
    )
    
    def importance_score_display(self, obj):
        color = 'red' if obj.importance_score > 0.7 else 'orange' if obj.importance_score > 0.4 else 'yellow'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color, obj.importance_score
        )
    importance_score_display.short_description = 'Importance'
    
    def claim_a_preview(self, obj):
        return obj.claim_a.claim_text[:60] + "..."
    claim_a_preview.short_description = 'Claim A'
    
    def claim_b_preview(self, obj):
        return obj.claim_b.claim_text[:60] + "..."
    claim_b_preview.short_description = 'Claim B'


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'reliability_score', 'bias_score', 'last_updated')
    list_filter = ('reliability_score', 'last_updated')
    search_fields = ('name',)
    fieldsets = (
        ('Source Info', {'fields': ('name', 'url')}),
        ('Credibility', {'fields': ('reliability_score', 'bias_score')}),
        ('Timestamps', {'fields': ('last_updated',)}),
    )

