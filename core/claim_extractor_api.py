"""
API-friendly wrapper functions for claim extraction.
These wrap the existing ClaimExtractor class to work with Django ORM models.
"""

from typing import List
from core.models import Claim, Content, Contradiction
from core.claim_extractor import ClaimExtractor, ContradictionDetector


def extract_claims(text: str, content: Content = None) -> List[Claim]:
    """Extract claims from text and save to database."""
    if not text or not content:
        return []
    
    raw_claims = ClaimExtractor.extract_claims(text, confidence_threshold=0.55)
    
    claim_objects = []
    for raw_claim in raw_claims:
        claim = Claim.objects.create(
            content=content,
            claim_text=raw_claim['claim_text'],
            confidence=raw_claim['confidence'],
            is_negated=raw_claim['is_negated'],
            has_qualifier=raw_claim['has_qualifier'],
        )
        claim_objects.append(claim)
    
    return claim_objects


def detect_contradictions(claims: List[Claim]):
    """Detect contradictions between claims and save to database."""
    if len(claims) < 2:
        return []
    
    contradictions_found = []
    claims_list = list(claims)
    
    # Compare each pair of claims
    for i in range(len(claims_list)):
        for j in range(i + 1, len(claims_list)):
            claim_a = claims_list[i]
            claim_b = claims_list[j]
            
            # Use ContradictionDetector to check for contradiction
            result = ContradictionDetector.detect_contradiction(
                claim_a.claim_text,
                claim_b.claim_text,
                claim1_negated=claim_a.is_negated,
                claim2_negated=claim_b.is_negated
            )
            
            # Only save if it's a real contradiction
            if result['is_contradiction']:
                try:
                    contradiction = Contradiction.objects.create(
                        claim_a=claim_a,
                        claim_b=claim_b,
                        importance_score=result['importance_score'],
                        contradiction_type=result['type'],
                        description=result['explanation']
                    )
                    contradictions_found.append(contradiction)
                    print(f"✅ Contradiction detected: {claim_a.claim_text[:50]}... vs {claim_b.claim_text[:50]}...")
                except Exception as e:
                    print(f"⚠️  Error saving contradiction: {str(e)}")
    
    return contradictions_found



def calculate_trust_score(claims: List[Claim], contradictions) -> float:
    """Calculate overall trust score for content."""
    if not claims:
        return 0.5
    
    avg_confidence = sum(c.confidence for c in claims) / len(claims)
    contradiction_count = len(contradictions) if contradictions else 0
    penalty = contradiction_count * 0.1
    score = max(0.0, min(1.0, avg_confidence - penalty))
    
    return round(score, 2)
