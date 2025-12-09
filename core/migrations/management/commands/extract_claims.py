from django.core.management.base import BaseCommand
from core.models import Content, Claim, Contradiction
from core.claim_extractor import ClaimExtractor, ContradictionDetector


class Command(BaseCommand):
    help = 'Extract claims from all Content objects that don\'t have claims yet'
    
    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Re-extract claims from ALL content')
    
    def handle(self, *args, **options):
        if options['all']:
            contents = Content.objects.all()
            self.stdout.write(self.style.WARNING(f'Re-extracting claims from {contents.count()} content items...'))
        else:
            contents = Content.objects.filter(claims__isnull=True).distinct()
            self.stdout.write(f'Extracting claims from {contents.count()} content items...')
        
        for i, content in enumerate(contents, 1):
            # Skip if already has claims (unless --all)
            if not options['all'] and content.claims.exists():
                continue
            
            # Extract claims
            extracted_claims = ClaimExtractor.extract_claims(content.raw_text)
            
            if not extracted_claims:
                self.stdout.write(f'  [{i}] Content #{content.id}: No claims found')
                continue
            
            # Create Claim objects
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
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'  [{i}] Content #{content.id}: Extracted {len(created_claims)} claims, trust_score: {content.trust_score}'
                )
            )
        
        self.stdout.write(self.style.SUCCESS('✓ Claim extraction complete!'))
