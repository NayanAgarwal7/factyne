from celery import shared_task
from django.utils import timezone
from core.models import Content, Claim, Contradiction
from core.claim_extractor_v2 import AdvancedClaimExtractor
from core.claim_extractor import ContradictionDetector
from core.external_verifier import ExternalFactChecker
from core.audit_log import AuditLog
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_content_async(self, content_id):
    """
    Async task: extract claims, detect contradictions, verify externally,
    recalculate trust score, and log everything.
    """
    try:
        content = Content.objects.get(id=content_id)
        raw_text = content.raw_text

        # Extract claims
        extracted_claims = AdvancedClaimExtractor.extract_claims(raw_text)

        created_claims = []
        if extracted_claims:
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
                            contradiction, _ = Contradiction.objects.update_or_create(
                                claim_a=new_claim,
                                claim_b=existing,
                                defaults={
                                    'importance_score': info['importance_score'],
                                    'contradiction_type': info['type'],
                                    'description': info['explanation'],
                                },
                            )

                            AuditLog.log_contradiction(
                                contradiction.id,
                                new_claim.id,
                                existing.id,
                                info['importance_score'],
                                info['type'],
                            )
                            break

        # External verification for each claim
        for claim in created_claims:
            verify_claim_externally.delay(claim.id)

        # Recalculate trust score
        content.calculate_trust_score()

        AuditLog.log_event(
            'async_processing_complete',
            content.id,
            'Content',
            {
                'trust_score': content.trust_score,
                'contradiction_count': content.contradiction_count,
                'claims_count': len(created_claims),
            },
        )

        return {'status': 'success', 'claims': len(created_claims)}

    except Exception as exc:
        logger.error(f"Error processing content {content_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=2)
def verify_claim_externally(self, claim_id):
    """
    Verify a single claim against external sources (Wikipedia, etc.).
    """
    try:
        claim = Claim.objects.get(id=claim_id)
        verification = ExternalFactChecker.verify_claim(claim.claim_text)

        # Adjust confidence based on verification flags
        if verification.get('verified'):
            claim.confidence = min(1.0, claim.confidence + 0.15)
        elif verification.get('refuted'):
            claim.confidence = max(0.0, claim.confidence - 0.25)

        claim.save()

        AuditLog.log_event(
            'external_verification',
            claim.id,
            'Claim',
            {
                'verified': verification.get('verified', False),
                'refuted': verification.get('refuted', False),
                'source_count': len(verification.get('sources', [])),
            },
        )

        return {'claim_id': claim_id, 'verified': verification.get('verified', False)}

    except Exception as exc:
        logger.error(f"Error verifying claim {claim_id}: {exc}")
        raise self.retry(exc=exc, countdown=120)
