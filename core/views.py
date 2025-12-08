from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q, Avg, Count
from core.models import Content, Claim, Contradiction
from core.claim_extractor import ClaimExtractor, ContradictionDetector
from api.serializers import ClaimSerializer


def submit_page(request):
    """Submit content via web form."""
    result = None
    
    if request.method == 'POST':
        raw_text = request.POST.get('raw_text', '').strip()
        url = request.POST.get('url', '').strip() or None
        
        if not raw_text:
            messages.error(request, 'Please provide content to check.')
            return redirect('submit_page')
        
        # Create Content
        content = Content.objects.create(
            raw_text=raw_text,
            url=url,
            user=request.user if request.user.is_authenticated else None
        )
        
        # Extract claims
        extracted_claims = ClaimExtractor.extract_claims(raw_text)
        
        if extracted_claims:
            created_claims = []
            for extracted_claim in extracted_claims:
                claim = Claim.objects.create(
                    content=content,
                    claim_text=extracted_claim['claim_text'],
                    confidence=extracted_claim['confidence'],
                    is_negated=extracted_claim['is_negated'],
                    has_qualifier=extracted_claim['has_qualifier'],
                )
                created_claims.append(claim)
            
            # Detect contradictions
            all_existing_claims = Claim.objects.exclude(content=content)
            
            for new_claim in created_claims:
                contradictions_found = ContradictionDetector.detect_contradictions_batch(
                    new_claim.claim_text,
                    [{
                        'claim_text': c.claim_text,
                        'is_negated': c.is_negated
                    } for c in all_existing_claims]
                )
                
                for contradiction_info in contradictions_found:
                    for existing_claim in all_existing_claims:
                        if existing_claim.claim_text == contradiction_info['existing_claim_text']:
                            Contradiction.objects.update_or_create(
                                claim_a=new_claim,
                                claim_b=existing_claim,
                                defaults={
                                    'importance_score': contradiction_info['importance_score'],
                                    'contradiction_type': contradiction_info['type'],
                                    'description': contradiction_info['explanation'],
                                }
                            )
                            break
        
        # Recalculate trust score
        content.calculate_trust_score()
        
        messages.success(request, 'Content processed successfully!')
        
        result = {
            'id': content.id,
            'raw_text': content.raw_text,
            'trust_score': content.trust_score,
            'trust_explanation': content.trust_explanation,
            'claims': ClaimSerializer(content.claims.all(), many=True).data,
            'contradiction_count': content.contradiction_count,
        }
    
    return render(request, 'submit.html', {'result': result})


def dashboard(request):
    """Dashboard with stats."""
    contents = Content.objects.all()[:20]
    
    stats = {
        'total_content': Content.objects.count(),
        'avg_trust_score': Content.objects.aggregate(avg=Avg('trust_score'))['avg'] or 0,
        'total_claims': Claim.objects.count(),
        'total_contradictions': Contradiction.objects.count(),
        'contents': contents,
    }
    
    return render(request, 'dashboard.html', stats)


def api_docs(request):
    """API documentation page."""
    return render(request, 'api_docs.html')
