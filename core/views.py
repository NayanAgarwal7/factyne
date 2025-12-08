from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
from core.models import Content, Claim, Contradiction
from core.source_credibility import SourceCredibilityEngine
from core.audit_log import AuditLog
from api.serializers import ClaimSerializer
from core.tasks import process_content_async
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
import logging

logger = logging.getLogger(__name__)


def content_detail(request, content_id):
    """Show detailed analysis of a single content submission."""
    content = get_object_or_404(Content, id=content_id)
    claims = Claim.objects.filter(content=content)

    # Use claim_a / claim_b from your model
    contradictions = Contradiction.objects.filter(
        claim_a__content=content
    ) | Contradiction.objects.filter(
        claim_b__content=content
    )

    data = {
        'content': content,
        'claims': claims,
        'contradictions': contradictions,
        'total_claims': claims.count(),
        'avg_confidence': claims.aggregate(avg=Avg('confidence'))['avg'] or 0,
    }
    return render(request, 'content_detail.html', data)


def content_pdf(request, content_id):
    """Export a single content analysis as PDF using xhtml2pdf."""
    content = get_object_or_404(Content, id=content_id)
    claims = Claim.objects.filter(content=content)

    contradictions = Contradiction.objects.filter(
        claim_a__content=content
    ) | Contradiction.objects.filter(
        claim_b__content=content
    )

    context = {
        'content': content,
        'claims': claims,
        'contradictions': contradictions,
        'total_claims': claims.count(),
        'avg_confidence': claims.aggregate(avg=Avg('confidence'))['avg'] or 0,
        'now': timezone.now(),
    }

    # Render HTML template
    html_string = render_to_string('content_pdf.html', context)

    # Generate PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="content_{content_id}.pdf"'

    pisa.CreatePDF(html_string, response)
    return response


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
            # Redirect to detail page instead of showing result
            return redirect('content_detail', content_id=recent_duplicate.id)

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
        # Redirect to detail page instead of dashboard
        return redirect('content_detail', content_id=content.id)

    return render(request, 'submit.html', {'result': result})


def dashboard(request):
    """Dashboard with search and filter."""
    contents = Content.objects.all().order_by('-created_at')

    # Search by content text
    search_query = request.GET.get('search', '').strip()
    if search_query:
        contents = contents.filter(raw_text__icontains=search_query)

    # Filter by trust score range
    min_score = request.GET.get('min_score', '')
    max_score = request.GET.get('max_score', '')

    if min_score:
        try:
            contents = contents.filter(trust_score__gte=float(min_score))
        except ValueError:
            pass

    if max_score:
        try:
            contents = contents.filter(trust_score__lte=float(max_score))
        except ValueError:
            pass

    contents = contents[:20]  # Latest 20

    data = {
        'total_content': Content.objects.count(),
        'avg_trust_score': Content.objects.aggregate(avg=Avg('trust_score'))['avg'] or 0,
        'total_claims': Claim.objects.count(),
        'total_contradictions': Contradiction.objects.count(),
        'contents': contents,
        'search_query': search_query,
        'min_score': min_score,
        'max_score': max_score,
    }
    return render(request, 'dashboard.html', data)


def api_docs(request):
    return render(request, 'api_docs.html')
