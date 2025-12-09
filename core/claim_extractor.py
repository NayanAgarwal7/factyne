import re
from typing import List, Dict
from difflib import SequenceMatcher


class ClaimExtractor:
    """
    Advanced claim extraction from text using:
    - Sentence parsing
    - Keyword patterns
    - Linguistic heuristics
    - Confidence scoring
    """
    
    CLAIM_KEYWORDS = [
        r'\b(is|are|was|were)\s+',
        r'\b(has|have|had)\s+',
        r'\b(says|claims|states|reports|shows|proves|demonstrates|indicates|suggests)\s+',
        r'\b(\d+%|\d+\s*(percent|billion|million|thousand|years|months|days|hours))\s+',
        r'\b(according to|studies show|research indicates|data shows|evidence suggests|findings show)\s+',
        r'\b(vaccine|covid|pandemic|disease|virus|treatment|drug|medicine|therapy|symptom)\s+',
        r'\b(government|company|organization|agency|institution|university|hospital|media)\s+',
        r'\b(temperature|climate|weather|global|warming|emissions|carbon|pollution)\s+',
        r'\b(cause|caused|causes|leading to|results in|leads to|contribute|contributed|contributing)\s+',
        r'\b(increase|increased|increases|decrease|decreased|decreases|rise|drop|fall)\s+',
        r'\b(safe|unsafe|dangerous|effective|ineffective|works|fails|successful|failure)\s+',
        r'\b(risk|risks|benefit|benefits|side.?effect|adverse|harmful|beneficial)\s+',
        r'\b(new|latest|recent|study|research|report|investigation|analysis|findings)\s+',
    ]

    NEGATION_WORDS = ['not', 'no', 'never', 'neither', 'nobody', 'nothing', 'nowhere', 'cannot']
    QUALIFIERS = ['may', 'might', 'could', 'possibly', 'probably', 'allegedly', 'reportedly', 'seems', 'appears']
    
    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """Split into sentences, filter short ones."""
        sentences = re.split(r'[.!?]\s+', text)
        return [s.strip() for s in sentences if len(s.strip()) > 15]
    
    @staticmethod
    def is_claim_sentence(sentence: str) -> bool:
        """Heuristic: does this look like a factual claim?"""
        lower = sentence.lower()
        
        # Check keywords
        for pattern in ClaimExtractor.CLAIM_KEYWORDS:
            if re.search(pattern, lower):
                return True
        
        # Check for named entities / important words
        important = ['covid', 'vaccine', 'study', 'research', 'data', 'report', 'found', 'showed', 'discovered', 'proved']
        if any(word in lower for word in important):
            return True
        
        # Check for numbers (statistics)
        if re.search(r'\d+', sentence):
            return True
        
        return False
    
    @staticmethod
    def extract_claims(text: str, confidence_threshold: float = 0.50) -> List[Dict]:
        """Extract claims with confidence scoring."""
        sentences = ClaimExtractor.extract_sentences(text)
        claims = []
        
        for sentence in sentences:
            if not ClaimExtractor.is_claim_sentence(sentence):
                continue
            
            lower = sentence.lower()
            
            # Negation detection
            is_negated = any(word in lower for word in ClaimExtractor.NEGATION_WORDS)
            
            # Qualifier detection
            has_qualifier = any(word in lower for word in ClaimExtractor.QUALIFIERS)
            
            # Base confidence
            confidence = 0.75
            
            if is_negated:
                confidence -= 0.15
            if has_qualifier:
                confidence -= 0.1
            
            # Boost for length (more detail = higher confidence)
            word_count = len(sentence.split())
            if word_count > 20:
                confidence += 0.1
            elif word_count < 10:
                confidence -= 0.1
            
            # Boost for numbers/statistics
            if re.search(r'\d+', sentence):
                confidence += 0.05
            
            confidence = max(0.35, min(1.0, confidence))
            
            if confidence >= confidence_threshold:
                claims.append({
                    'claim_text': sentence.strip(),
                    'confidence': round(confidence, 2),
                    'is_negated': is_negated,
                    'has_qualifier': has_qualifier,
                })
        
        return claims
    
    @staticmethod
    def extract_keywords(claim_text: str) -> List[str]:
        """Extract keywords for similarity matching."""
        words = claim_text.lower().split()
        stopwords = {
            'is', 'are', 'was', 'were', 'the', 'a', 'an', 'and', 'or', 'but',
            'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
            'be', 'been', 'being'
        }
        keywords = [w.strip('.,!?;:') for w in words if len(w) > 3 and w not in stopwords]
        return list(set(keywords))[:15]


class ContradictionDetector:
    """
    Detect logical contradictions between claims using:
    - Keyword overlap
    - Negation analysis
    - Similarity matching
    """

    @staticmethod
    def similarity_ratio(text1: str, text2: str) -> float:
        """Calculate text similarity (0.0-1.0)."""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    @staticmethod
    def keyword_overlap(claim1: str, claim2: str) -> float:
        """Calculate overlap in keywords (0.0-1.0)."""
        kw1 = set(ClaimExtractor.extract_keywords(claim1))
        kw2 = set(ClaimExtractor.extract_keywords(claim2))
        
        if not kw1 or not kw2:
            return 0.0
        
        overlap = len(kw1 & kw2)
        total = len(kw1 | kw2)
        return overlap / total if total > 0 else 0.0

    @staticmethod
    def _normalize_token(word: str) -> str:
        """Very simple stemming/normalization for contradiction checks."""
        word = word.lower().strip('.,!?;:()[]{}"\'')
        for suffix in ['ing', 'ed', 'es', 's']:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)]
        return word

    @staticmethod
    def detect_contradiction(
        claim1_text: str,
        claim2_text: str,
        claim1_negated: bool = False,
        claim2_negated: bool = False
    ) -> Dict:
        """
        Detect if two claims contradict. Returns:
        - is_contradiction: bool
        - importance_score: 0.0-1.0 (how serious is this contradiction?)
        - type: 'direct_negation', 'semantic', 'statistical', 'none'
        - explanation: human-readable description
        """
        # Direct negation: same-ish claim, opposite negation
        similarity = ContradictionDetector.similarity_ratio(claim1_text, claim2_text)
        keyword_overlap = ContradictionDetector.keyword_overlap(claim1_text, claim2_text)

        # Rule 1: High similarity + opposite negation = direct contradiction
        if similarity > 0.5 and claim1_negated != claim2_negated:
            return {
                'is_contradiction': True,
                'type': 'direct_negation',
                'importance_score': round(min(1.0, 0.8 + (keyword_overlap * 0.2)), 2),
                'explanation': f'Direct contradiction: one claims something, the other denies it (similarity: {round(similarity, 2)})'
            }

        # Rule 2: Good keyword overlap + opposite logical direction
        if keyword_overlap > 0.3:
            # Normalize tokens
            lower1 = claim1_text.lower()
            lower2 = claim2_text.lower()
            tokens1 = [ContradictionDetector._normalize_token(w) for w in lower1.split()]
            tokens2 = [ContradictionDetector._normalize_token(w) for w in lower2.split()]

            opposites = [
                ('increase', 'decrease'),
                ('rise', 'fall'),
                ('up', 'down'),
                ('safe', 'dangerous'),
                ('effective', 'ineffective'),
                ('true', 'false'),
                ('yes', 'no'),
                ('support', 'oppose'),
                ('help', 'harm'),
                ('benefit', 'harm'),
                ('flat', 'spherical'),
            ]

            for word1, word2 in opposites:
                w1 = ContradictionDetector._normalize_token(word1)
                w2 = ContradictionDetector._normalize_token(word2)
                if (w1 in tokens1 and w2 in tokens2) or (w2 in tokens1 and w1 in tokens2):
                    return {
                        'is_contradiction': True,
                        'type': 'semantic',
                        'importance_score': round(0.7 + (keyword_overlap * 0.25), 2),
                        'explanation': f'Semantic contradiction: claims use opposite concepts (keywords: {keyword_overlap:.0%} overlap)'
                    }

        # Rule 3: Specific numbers in conflict
        numbers1 = re.findall(r'\d+', claim1_text)
        numbers2 = re.findall(r'\d+', claim2_text)

        if numbers1 and numbers2 and keyword_overlap > 0.2:
            try:
                if numbers1[0] != numbers2[0]:
                    return {
                        'is_contradiction': True,
                        'type': 'statistical',
                        'importance_score': round(0.65 + (keyword_overlap * 0.3), 2),
                        'explanation': f'Statistical discrepancy: different numbers reported ({numbers1[0]} vs {numbers2[0]})'
                    }
            except Exception:
                pass

        # No contradiction
        return {
            'is_contradiction': False,
            'type': 'none',
            'importance_score': 0.0,
            'explanation': 'No clear contradiction detected'
        }

    @staticmethod
    def detect_contradictions_batch(new_claim_text: str, existing_claims: List[Dict]) -> List[Dict]:
        """
        Find all contradictions between a new claim and existing claims.
        
        Args:
            new_claim_text: the new claim to check
            existing_claims: list of dicts with 'claim_text' and 'is_negated'
        
        Returns: list of contradictions found
        """
        contradictions = []
        
        for existing_claim in existing_claims:
            result = ContradictionDetector.detect_contradiction(
                new_claim_text,
                existing_claim['claim_text'],
                claim1_negated=False,  # assume new claim is not negated (refactor as needed)
                claim2_negated=existing_claim.get('is_negated', False)
            )
            
            if result['is_contradiction']:
                contradictions.append({
                    'existing_claim_text': existing_claim['claim_text'],
                    'new_claim_text': new_claim_text,
                    **result
                })
        
        return contradictions
