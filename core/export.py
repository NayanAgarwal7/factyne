from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from django.http import HttpResponse
import json
from core.models import Content


class ReportExporter:
    """Export content analysis as PDF or JSON."""
    
    @staticmethod
    def export_pdf(content_id: int) -> HttpResponse:
        """Generate PDF report for a content submission."""
        content = Content.objects.get(id=content_id)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="factyne_report_{content_id}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        story.append(Paragraph(f"Factyne Report #{content.id}", styles['Title']))
        story.append(Spacer(1, 0.2*inch))
        
        # Trust Score
        story.append(Paragraph(f"<b>Trust Score:</b> {content.trust_score:.2f}", styles['Normal']))
        story.append(Paragraph(f"<b>Explanation:</b> {content.trust_explanation}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Claims
        story.append(Paragraph(f"<b>Extracted Claims ({content.claims.count()}):</b>", styles['Heading2']))
        
        for claim in content.claims.all():
            story.append(Paragraph(f"• {claim.claim_text}", styles['Normal']))
            story.append(Paragraph(f"  Confidence: {claim.confidence:.0%}", styles['Italic']))
            story.append(Spacer(1, 0.1*inch))
        
        doc.build(story)
        return response
    
    @staticmethod
    def export_json(content_id: int) -> HttpResponse:
        """Export as JSON."""
        content = Content.objects.get(id=content_id)
        
        data = {
            'id': content.id,
            'raw_text': content.raw_text,
            'url': content.url,
            'trust_score': content.trust_score,
            'trust_explanation': content.trust_explanation,
            'contradiction_count': content.contradiction_count,
            'created_at': content.created_at.isoformat(),
            'claims': [
                {
                    'claim_text': c.claim_text,
                    'confidence': c.confidence,
                    'is_negated': c.is_negated,
                    'has_qualifier': c.has_qualifier,
                    'evidence_summary': c.evidence_summary,
                }
                for c in content.claims.all()
            ],
        }
        
        response = HttpResponse(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="factyne_report_{content_id}.json"'
        return response
