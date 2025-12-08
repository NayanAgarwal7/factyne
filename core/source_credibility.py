import logging
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta
from core.models import Source, Claim, Contradiction
from django.db.models import Avg, Count, Q

logger = logging.getLogger(__name__)


class SourceCredibilityEngine:
    """
    Compute and update source credibility based on:
    - Historical accuracy (% of claims not contradicted)
    - Recency (recent claims weight more)
    - Claims-per-domain (breadth)
    - User/expert feedback (if available)
    """

    # Weights for different factors
    WEIGHTS = {
        'accuracy': 0.4,  # biggest factor
        'recency': 0.2,
        'breadth': 0.15,
        'bias': 0.15,  # measured bias correction
        'base': 0.1,  # prior / baseline
    }

    @staticmethod
    def compute_source_reliability(source: Source) -> Tuple[float, Dict[str, Any]]:
        """
        Compute reliability score (0-1) for a source.
        Returns (score, breakdown_dict).
        """
        breakdown = {}

        # 1. Accuracy: % of claims not contradicted
        accuracy_score = SourceCredibilityEngine._compute_accuracy(source)
        breakdown['accuracy'] = accuracy_score

        # 2. Recency: recent claims matter more
        recency_score = SourceCredibilityEngine._compute_recency(source)
        breakdown['recency'] = recency_score

        # 3. Breadth: how many different topics/domains
        breadth_score = SourceCredibilityEngine._compute_breadth(source)
        breakdown['breadth'] = breadth_score

        # 4. Bias: estimate left/right lean (0=left, 0.5=neutral, 1=right)
        bias_score = SourceCredibilityEngine._compute_bias(source)
        breakdown['bias'] = bias_score

        # 5. Base score (start with 0.5 = neutral)
        base_score = 0.5
        breakdown['base'] = base_score

        # Weighted average
        final_score = (
            accuracy_score * SourceCredibilityEngine.WEIGHTS['accuracy']
            + recency_score * SourceCredibilityEngine.WEIGHTS['recency']
            + breadth_score * SourceCredibilityEngine.WEIGHTS['breadth']
            + ((1 - abs(bias_score - 0.5) * 2))
            * SourceCredibilityEngine.WEIGHTS['bias']  # penalize extreme bias
            + base_score * SourceCredibilityEngine.WEIGHTS['base']
        )

        breakdown['final_score'] = final_score
        breakdown['last_computed'] = datetime.now()

        logger.info(f"Source {source.name}: reliability = {final_score:.3f}, {breakdown}")
        return final_score, breakdown

    @staticmethod
    def _compute_accuracy(source: Source) -> float:
        """Accuracy = (non-contradicted claims) / (total claims)."""
        claims = Claim.objects.filter(source=source)
        if not claims.exists():
            return 0.5  # neutral if no claims

        total = claims.count()
        contradicted = Contradiction.objects.filter(
            Q(claim_a__source=source) | Q(claim_b__source=source)
        ).count()

        accuracy = 1.0 - (contradicted / total) if total > 0 else 0.5
        return max(0.0, min(1.0, accuracy))

    @staticmethod
    def _compute_recency(source: Source) -> float:
        """Recency: claims from last 30 days matter more."""
        now = datetime.now()
        claims = Claim.objects.filter(source=source)

        if not claims.exists():
            return 0.5

        recent_30d = claims.filter(
            created_at__gte=now - timedelta(days=30)
        ).count()
        total = claims.count()

        recency = (recent_30d / total) if total > 0 else 0.5
        return recency

    @staticmethod
    def _compute_breadth(source: Source) -> float:
        """Breadth: log scale of unique topics/domains covered."""
        claims = Claim.objects.filter(source=source)
        unique_content_ids = claims.values('content_id').distinct().count()

        # Breadth: log2(unique_topics) / 10 (normalized)
        import math

        breadth = min(1.0, math.log2(unique_content_ids + 1) / 10)
        return breadth

    @staticmethod
    def _compute_bias(source: Source) -> float:
        """Estimate bias by analyzing claim polarity distribution."""
        from textblob import TextBlob

        claims = Claim.objects.filter(source=source)[:100]  # sample
        if not claims.exists():
            return 0.5

        polarities = []
        for claim in claims:
            try:
                blob = TextBlob(claim.claim_text)
                polarities.append(blob.sentiment.polarity)
            except:
                pass

        if not polarities:
            return 0.5

        avg_polarity = sum(polarities) / len(polarities)
        # Convert -1..1 range to 0..1 bias scale
        bias = (avg_polarity + 1) / 2
        return bias

    @staticmethod
    def update_all_sources():
        """Bulk update reliability scores for all sources."""
        sources = Source.objects.all()
        updates = 0

        for source in sources:
            score, breakdown = SourceCredibilityEngine.compute_source_reliability(source)
            source.reliability_score = score
            source.save(update_fields=['reliability_score'])
            updates += 1

        logger.info(f"Updated {updates} sources")
        return updates
