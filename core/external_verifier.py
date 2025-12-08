import requests
import wikipediaapi
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ExternalFactChecker:
    """
    Verify claims against external sources:
    - Wikipedia API
    - Google Fact Check API (optional, needs API key)
    - Custom fact-checking databases
    """
    
    GOOGLE_FACT_CHECK_API = 'https://factchecktools.googleapis.com/v1alpha1/claims:search'
    
    @staticmethod
    def verify_claim(claim_text: str) -> Dict[str, Any]:
        """
        Main verification method. Returns verification result with sources.
        """
        results = {
            'claim': claim_text,
            'verified': False,
            'refuted': False,
            'sources': [],
            'confidence': 0.5,
        }
        
        # 1. Check Wikipedia
        wiki_results = ExternalFactChecker._check_wikipedia(claim_text)
        if wiki_results:
            results['sources'].extend(wiki_results)
            results['verified'] = True
            results['confidence'] += 0.2
        
        # 2. Check Google Fact Check (if API key available)
        # Uncomment if you have API key
        # google_results = ExternalFactChecker._check_google_factcheck(claim_text)
        # if google_results:
        #     results['sources'].extend(google_results)
        
        return results
    
    @staticmethod
    def _check_wikipedia(claim_text: str) -> List[Dict[str, Any]]:
        """Search Wikipedia for related articles."""
        try:
            wiki = wikipediaapi.Wikipedia('Factyne/1.0', 'en')
            
            # Extract key terms from claim
            keywords = claim_text.split()[:5]  # simple keyword extraction
            search_query = ' '.join(keywords)
            
            # Try to find a page
            page = wiki.page(search_query)
            
            if page.exists():
                return [{
                    'source': 'Wikipedia',
                    'url': page.fullurl,
                    'snippet': page.summary[:200],
                    'confidence': 0.7,
                }]
            
            return []
            
        except Exception as e:
            logger.error(f"Wikipedia lookup error: {e}")
            return []
    
    @staticmethod
    def _check_google_factcheck(claim_text: str, api_key: str = None) -> List[Dict[str, Any]]:
        """
        Check Google Fact Check Tools API.
        Requires API key from https://developers.google.com/fact-check/tools/api
        """
        if not api_key:
            return []
        
        try:
            params = {
                'query': claim_text,
                'key': api_key,
            }
            
            response = requests.get(
                ExternalFactChecker.GOOGLE_FACT_CHECK_API,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for claim in data.get('claims', [])[:3]:
                    for review in claim.get('claimReview', []):
                        results.append({
                            'source': review.get('publisher', {}).get('name', 'Unknown'),
                            'url': review.get('url'),
                            'snippet': review.get('textualRating'),
                            'confidence': 0.8,
                        })
                
                return results
            
            return []
            
        except Exception as e:
            logger.error(f"Google Fact Check error: {e}")
            return []
