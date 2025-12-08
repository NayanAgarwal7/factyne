import re
import spacy
from typing import List, Dict, Any
from textblob import TextBlob
import logging

logger = logging.getLogger(__name__)

try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
    logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None


class AdvancedClaimExtractor:
    """
    Extract structured claims using:
    - Named Entity Recognition (NER)
    - Dependency parsing
    - Sentiment/polarity analysis
    - Pattern matching
    """

    # Common qualifier patterns (reduce confidence)
    QUALIFIER_PATTERNS = [
        r'\b(may|might|could|possibly|perhaps|allegedly|reportedly)\b',
        r'\b(seem|appear|suggest|indicate|tend to)\b',
        r'\b(some|many|most|few|several)\s+\w+',
        r'\b(it is believed that|it is thought that)\b',
    ]

    # Negation patterns
    NEGATION_PATTERNS = [
        r'\b(not|no|never|neither|nor)\b',
        r'\b(doesn\'t|don\'t|didn\'t|won\'t|can\'t|couldn\'t)\b',
        r'\b(fails to|failed to)\b',
    ]

    # Strong assertion patterns (increase confidence)
    ASSERTION_PATTERNS = [
        r'\b(proves|proven|definitely|certainly|clearly|obviously)\b',
        r'\b(must|will|always|never)\s+',
        r'\b(is|are)\s+\w+\b',  # simple factual statements
    ]

    @staticmethod
    def extract_claims(text: str, min_length: int = 10) -> List[Dict[str, Any]]:
        """
        Extract claims from text using multiple strategies.
        Returns list of claim dicts with confidence, flags, and source info.
        """
        if not text or len(text.strip()) < 20:
            logger.info(f"Text too short ({len(text)} chars)")
            return []

        claims = []

        # Strategy 1: Sentence-based extraction (always run)
        sentence_claims = AdvancedClaimExtractor._extract_from_sentences(text)
        claims.extend(sentence_claims)

        # Strategy 2: NER-based (entity relationships)
        if nlp:
            ner_claims = AdvancedClaimExtractor._extract_from_ner(text)
            claims.extend(ner_claims)

        # Strategy 3: Dependency parsing (subject-verb-object)
        if nlp:
            svo_claims = AdvancedClaimExtractor._extract_svo(text)
            claims.extend(svo_claims)

        # Deduplicate similar claims
        claims = AdvancedClaimExtractor._deduplicate_claims(claims)

        logger.info(f"Extracted {len(claims)} unique claims from {len(text.split())} words")
        return claims

    @staticmethod
    def _extract_from_sentences(text: str) -> List[Dict[str, Any]]:
        """Extract claims from declarative sentences."""
        sentences = text.split('.')
        claims = []

        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 10:
                continue

            # Analyze using TextBlob
            blob = TextBlob(sent)
            polarity = blob.sentiment.polarity  # -1 to 1

            # Check for qualifiers, negations, assertions
            is_negated = bool(
                re.search(
                    '|'.join(AdvancedClaimExtractor.NEGATION_PATTERNS),
                    sent,
                    re.IGNORECASE,
                )
            )
            has_qualifier = bool(
                re.search(
                    '|'.join(AdvancedClaimExtractor.QUALIFIER_PATTERNS),
                    sent,
                    re.IGNORECASE,
                )
            )
            has_assertion = bool(
                re.search(
                    '|'.join(AdvancedClaimExtractor.ASSERTION_PATTERNS),
                    sent,
                    re.IGNORECASE,
                )
            )

            # Calculate confidence
            confidence = 0.5  # baseline
            if has_assertion:
                confidence += 0.25
            if has_qualifier:
                confidence -= 0.15
            if is_negated:
                confidence -= 0.1
            if abs(polarity) > 0.5:
                confidence += 0.1  # opinionated claims are still claims

            confidence = max(0.2, min(1.0, confidence))

            claims.append(
                {
                    'claim_text': sent,
                    'confidence': confidence,
                    'is_negated': is_negated,
                    'has_qualifier': has_qualifier,
                    'source_type': 'sentence',
                    'polarity': polarity,
                }
            )

        return claims

    @staticmethod
    def _extract_from_ner(text: str) -> List[Dict[str, Any]]:
        """Extract claims based on named entities (PERSON, ORG, GPE, PRODUCT, etc.)."""
        if not nlp:
            return []

        doc = nlp(text)
        claims = []

        # Group entities with their context
        for ent in doc.ents:
            # Get a window around entity
            start, end = max(0, ent.start_char - 100), min(
                len(text), ent.end_char + 100
            )
            context = text[start : end].strip()

            # Skip very generic contexts
            if len(context) < 15:
                continue

            confidence = {
                'PERSON': 0.7,
                'ORG': 0.7,
                'GPE': 0.75,
                'PRODUCT': 0.6,
                'DATE': 0.8,
                'MONEY': 0.8,
                'PERCENT': 0.85,
            }.get(ent.label_, 0.5)

            claims.append(
                {
                    'claim_text': f"{ent.text} ({ent.label_}): {context}",
                    'confidence': confidence,
                    'is_negated': 'not' in context.lower(),
                    'has_qualifier': 'may' in context.lower(),
                    'source_type': 'entity',
                    'entity_label': ent.label_,
                }
            )

        return claims[:10]  # limit to top 10 entity claims

    @staticmethod
    def _extract_svo(text: str) -> List[Dict[str, Any]]:
        """Extract Subject-Verb-Object triples (structured claims)."""
        if not nlp:
            return []

        doc = nlp(text)
        claims = []

        for token in doc:
            # Look for verbs as claim centers
            if token.pos_ == 'VERB':
                subject = None
                obj = None

                # Find subject (nsubj dependency)
                for child in token.children:
                    if child.dep_ == 'nsubj':
                        subject = child.text
                    if child.dep_ in ['dobj', 'attr']:
                        obj = child.text

                if subject and obj:
                    claim_text = f"{subject} {token.text} {obj}"
                    claims.append(
                        {
                            'claim_text': claim_text,
                            'confidence': 0.65,
                            'is_negated': False,
                            'has_qualifier': False,
                            'source_type': 'svo',
                        }
                    )

        return claims[:5]  # limit SVO claims

    @staticmethod
    def _deduplicate_claims(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove near-duplicate claims (>90% similarity)."""
        if not claims:
            return []

        unique = []
        for claim in claims:
            is_duplicate = False
            claim_text_lower = claim['claim_text'].lower()

            for existing in unique:
                existing_lower = existing['claim_text'].lower()

                # Simple similarity: if one contains other or >85% word overlap
                if (
                    claim_text_lower in existing_lower
                    or existing_lower in claim_text_lower
                ):
                    is_duplicate = True
                    break

                # Word overlap check
                claim_words = set(claim_text_lower.split())
                existing_words = set(existing_lower.split())
                if claim_words and existing_words:
                    overlap = len(claim_words & existing_words) / len(
                        claim_words | existing_words
                    )
                    if overlap > 0.85:
                        is_duplicate = True
                        break

            if not is_duplicate:
                unique.append(claim)

        return unique
