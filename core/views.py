from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
from core.models import Content, Claim, Contradiction
from core.claim_extractor_v2 import AdvancedClaimExtractor
from core.source_credibility import SourceCredibilityEngine
from core.audit_log import AuditLog
from core.claim_extractor import ContradictionDetector
from api.serializers import ClaimSerializer
import logging

logger = logging.getLogger(__name__)


def submit_page(request):
    """Submit content via web form with advanced extraction."""
    result = None

    if request.method == 'POST':
        raw_text = request.POST.get('raw_text', '').strip()
        url = request.POST.get('url', '').strip() or None

        if not raw_text:
            messages.error(request, 'Please provide content to check.')
            return redirect('submit_page')

        # Check for recent duplicate submissions
        recent_duplicate = Content.objects.filter(
            raw_text=raw_text,
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).first()

        if recent_duplicate:
            messages.warning(
                request,
                f'This content was already submitted on {recent_duplicate.created_at.strftime("%b %d, %Y at %H:%M")}. '
                f'Reusing previous analysis: Trust Score {recent_duplicate.trust_score:.2f}'
            )
            result = {
                'id': recent_duplicate.id,
                'raw_text': recent_duplicate.raw_text,
                'trust_score': recent_duplicate.trust_score,
                'trust_explanation': recent_duplicate.trust_explanation,
                'claims': ClaimSerializer(recent_duplicate.claims.all(), many=True).data,
                'contradiction_count': recent_duplicate.contradiction_count,
            }
            return render(request, 'submit.html', {'result': result})

        # Create Content
        content = Content.objects.create(
            raw_text=raw_text,
            url=url,
            user=request.user if request.user.is_authenticated else None,
        )

        # Log submission
        AuditLog.log_content_submission(
            content.id,
            url,
            len(raw_text.split()),
            request.user.id if request.user.is_authenticated else None,
        )

        # Extract claims using advanced extractor
        extracted_claims = AdvancedClaimExtractor.extract_claims(raw_text)

        if extracted_claims:
            created_claims = []
            for ec in extracted_claims:
                claim = Claim.objects.create(
                    content=content,
                    claim_text=ec['claim_text'],
                    confidence=ec['confidence'],
                    is_negated=ec.get('is_negated', False),
                    has_qualifier=ec.get('has_qualifier', False),
                )
                created_claims.append(claim)

            # Log extraction
            avg_conf = sum(c.confidence for c in created_claims) / len(created_claims)
            AuditLog.log_claims_extracted(content.id, len(created_claims), avg_conf)

            # Detect contradictions
            all_existing = Claim.objects.exclude(content=content)

            for new_claim in created_claims:
                contradictions_found = ContradictionDetector.detect_contradictions_batch(
                    new_claim.claim_text,
                    [
                        {'claim_text': c.claim_text, 'is_negated': c.is_negated}
                        for c in all_existing
                    ],
                )

                for info in contradictions_found:
                    for existing in all_existing:
                        if existing.claim_text == info['existing_claim_text']:
                            contradiction = Contradiction.objects.update_or_create(
                                claim_a=new_claim,
                                claim_b=existing,
                                defaults={
                                    'importance_score': info['importance_score'],
                                    'contradiction_type': info['type'],
                                    'description': info['explanation'],
                                },
                            )[0]

                            # Log contradiction
                            AuditLog.log_contradiction(
                                contradiction.id,
                                new_claim.id,
                                existing.id,
                                info['importance_score'],
                                info['type'],
                            )
                            break

        # Recalculate trust score
        content.calculate_trust_score()

        # Log score
        AuditLog.log_event(
            'score_calculated',
            content.id,
            'Content',
            {
                'trust_score': content.trust_score,
                'contradiction_count': content.contradiction_count,
            },
        )

        # Prepare result
        result = {
            'id': content.id,
            'raw_text': content.raw_text,
            'trust_score': content.trust_score,
            'trust_explanation': content.trust_explanation,
            'claims': ClaimSerializer(content.claims.all(), many=True).data,
            'contradiction_count': content.contradiction_count,
        }
        messages.success(request, 'Content processed successfully!')

    return render(request, 'submit.html', {'result': result})


def dashboard(request):
    """Dashboard with enhanced stats."""
    contents = Content.objects.all().order_by('-created_at')[:20]

    # Update all source scores (optional: run on schedule)
    # SourceCredibilityEngine.update_all_sources()

    data = {
        'total_content': Content.objects.count(),
        'avg_trust_score': Content.objects.aggregate(avg=Avg('trust_score'))['avg'] or 0,
        'total_claims': Claim.objects.count(),
        'total_contradictions': Contradiction.objects.count(),
        'contents': contents,
    }
    return render(request, 'dashboard.html', data)


def api_docs(request):
    return render(request, 'api_docs.html')
