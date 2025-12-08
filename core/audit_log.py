import logging
import json
import os
from datetime import datetime
from typing import Any, Dict

# Create logs folder if missing
os.makedirs('logs', exist_ok=True)

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/factyne.log'),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger('factyne_audit')


class AuditLog:
    """
    Track all major events: content submission, claim extraction, contradictions,
    source updates, user actions.
    """

    # Event types
    EVENT_CONTENT_SUBMITTED = 'content_submitted'
    EVENT_CLAIMS_EXTRACTED = 'claims_extracted'
    EVENT_CONTRADICTION_DETECTED = 'contradiction_detected'
    EVENT_SOURCE_UPDATED = 'source_updated'
    EVENT_SCORE_CALCULATED = 'score_calculated'
    EVENT_EVIDENCE_ADDED = 'evidence_added'

    @staticmethod
    def log_event(
        event_type: str,
        entity_id: int,
        entity_type: str,
        details: Dict[str, Any],
        user_id: int = None,
    ):
        """Log a structured event."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'entity': {'id': entity_id, 'type': entity_type},
            'user_id': user_id,
            'details': details,
        }

        logger.info(json.dumps(log_entry))
        return log_entry

    @staticmethod
    def log_content_submission(content_id: int, url: str, word_count: int, user_id: int = None):
        """Log when content is submitted."""
        AuditLog.log_event(
            AuditLog.EVENT_CONTENT_SUBMITTED,
            content_id,
            'Content',
            {
                'url': url,
                'word_count': word_count,
            },
            user_id,
        )

    @staticmethod
    def log_claims_extracted(
        content_id: int, claim_count: int, avg_confidence: float, user_id: int = None
    ):
        """Log when claims are extracted."""
        AuditLog.log_event(
            AuditLog.EVENT_CLAIMS_EXTRACTED,
            content_id,
            'Content',
            {
                'claim_count': claim_count,
                'avg_confidence': avg_confidence,
            },
            user_id,
        )

    @staticmethod
    def log_contradiction(
        contradiction_id: int,
        claim_a_id: int,
        claim_b_id: int,
        score: float,
        cont_type: str,
    ):
        """Log when a contradiction is detected."""
        AuditLog.log_event(
            AuditLog.EVENT_CONTRADICTION_DETECTED,
            contradiction_id,
            'Contradiction',
            {
                'claim_a_id': claim_a_id,
                'claim_b_id': claim_b_id,
                'importance_score': score,
                'type': cont_type,
            },
        )

    @staticmethod
    def log_source_reliability_update(source_id: int, old_score: float, new_score: float):
        """Log source reliability updates."""
        AuditLog.log_event(
            AuditLog.EVENT_SOURCE_UPDATED,
            source_id,
            'Source',
            {
                'old_reliability_score': old_score,
                'new_reliability_score': new_score,
            },
        )
