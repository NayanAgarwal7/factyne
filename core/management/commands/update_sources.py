from django.core.management.base import BaseCommand
from core.source_credibility import SourceCredibilityEngine
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Recompute reliability scores for all sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed output',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting source reliability update...')
        count = SourceCredibilityEngine.update_all_sources()
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {count} sources'
            )
        )
