from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify  # ok if unused for now


class Content(models.Model):
    url = models.URLField(null=True, blank=True)
    raw_text = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    trust_score = models.FloatField(default=0.5)
    trust_explanation = models.TextField(blank=True, default="")  # NEW
    contradiction_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Content #{self.id} - {self.raw_text[:50]}... (score: {self.trust_score})"

    def calculate_trust_score(self):
        """Recalculate trust score and generate explanation."""
        claims = self.claims.all()
        if not claims.exists():
            self.trust_score = 0.5
            self.trust_explanation = "No claims extracted. Unable to assess."
            self.save(update_fields=['trust_score', 'trust_explanation'])
            return

        # Base score from claim confidence
        avg_confidence = sum(c.confidence for c in claims) / claims.count()

        # Penalty for contradictions
        from django.db import models as djmodels  # local alias to avoid confusion
        contradictions = Contradiction.objects.filter(
            djmodels.Q(claim_a__content=self) | djmodels.Q(claim_b__content=self)
        )

        contradiction_penalty = contradictions.count() * 0.1

        self.trust_score = max(0.0, min(1.0, avg_confidence - contradiction_penalty))
        self.contradiction_count = contradictions.count()

        # Build human-readable explanation
        explanation_parts = [
            f"Based on {claims.count()} extracted claims.",
            f"Average claim confidence: {avg_confidence:.0%}.",
        ]

        if contradictions.exists():
            explanation_parts.append(f"{contradictions.count()} contradiction(s) detected, lowering score.")
        else:
            explanation_parts.append("No contradictions found in existing content.")

        if avg_confidence > 0.8:
            explanation_parts.append("Language patterns suggest strong, well-supported assertions.")
        elif avg_confidence < 0.5:
            explanation_parts.append("Many claims are qualified or negated, reducing confidence.")

        self.trust_explanation = " ".join(explanation_parts)

        self.save(update_fields=['trust_score', 'contradiction_count', 'trust_explanation'])


class Claim(models.Model):
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='claims')
    claim_text = models.TextField()
    confidence = models.FloatField(default=0.5)
    is_negated = models.BooleanField(default=False)
    has_qualifier = models.BooleanField(default=False)
    source = models.ForeignKey('Source', on_delete=models.SET_NULL, null=True, blank=True)
    evidence_summary = models.TextField(blank=True, default="")  # NEW
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-confidence', '-created_at']

    def __str__(self):
        return f"{self.claim_text[:60]}... (conf: {self.confidence})"

    def generate_evidence_summary(self):
        """Generate human-readable evidence explanation."""
        evidence_list = self.evidence.all()

        if not evidence_list.exists():
            self.evidence_summary = "No evidence collected yet."
            return

        summaries = []
        for ev in evidence_list[:3]:
            if ev.evidence_type == 'pattern':
                summaries.append(f"Pattern: {ev.description}")
            elif ev.evidence_type == 'contradiction':
                summaries.append(f"Conflict: {ev.description}")
            else:
                summaries.append(ev.description)

        self.evidence_summary = " ".join(summaries)


class Evidence(models.Model):
    """Evidence linking a claim to supporting/refuting information."""
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='evidence')
    evidence_type = models.CharField(
        max_length=20,
        choices=[
            ('pattern', 'Linguistic Pattern'),
            ('source', 'External Source'),
            ('contradiction', 'Contradicts Claim'),
            ('keyword', 'Keyword Match'),
        ],
    )
    description = models.TextField()
    source_url = models.URLField(blank=True, null=True)
    weight = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.evidence_type}: {self.description[:50]}..."


class Contradiction(models.Model):
    TYPES = [
        ('direct_negation', 'Direct Negation'),
        ('semantic', 'Semantic Conflict'),
        ('statistical', 'Statistical Discrepancy'),
        ('unknown', 'Unknown'),
    ]

    claim_a = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='contradictions_as_a')
    claim_b = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='contradictions_as_b')
    importance_score = models.FloatField(default=0.5)
    contradiction_type = models.CharField(max_length=20, choices=TYPES, default='unknown')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('claim_a', 'claim_b')
        ordering = ['-importance_score']

    def __str__(self):
        return f"Contradiction (score: {self.importance_score}) - {self.contradiction_type}"


class Source(models.Model):
    name = models.CharField(max_length=255, unique=True)
    url = models.URLField(blank=True)
    reliability_score = models.FloatField(default=0.5)  # 0-1
    bias_score = models.FloatField(default=0.5)  # 0=left, 0.5=neutral, 1=right
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (reliability: {self.reliability_score})"
