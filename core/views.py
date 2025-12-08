from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
from core.models import Content, Claim, Contradiction
from core.source_credibility import SourceCredibilityEngine
from core.audit_log import AuditLog
from api.serializers import ClaimSerializer
from core.tasks import process_content_async
import logging

logger = logging.getLogger(__name__)


def submit_page(request):
    """Submit content via web form; heavy processing is async via Celery."""
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
                f'This content was already submitted on '
                f'{recent_duplicate.created_at.strftime("%b %d, %Y at %H:%M")}. '
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

        # Send to Celery for async processing
        process_content_async.delay(content.id)

        messages.info(request, 'Content submitted! Processing in background...')
        return redirect('dashboard')

    return render(request, 'submit.html', {'result': result})


def dashboard(request):
    """Dashboard with enhanced stats."""
    contents = Content.objects.all().order_by('-created_at')[:20]

    # SourceCredibilityEngine.update_all_sources()  # optional

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
