from django.core.management.base import BaseCommand
from core.task import CSVETLPipeline, run_adzuna_ingestion


class Command(BaseCommand):
    help = "Run the Job Market Intelligence ETL/ingestion pipeline to load CSV data or API data into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=2000,
            help='Chunk size for bulk database operations (default: 2000)'
        )
        parser.add_argument(
            '--source',
            type=str,
            choices=['csv', 'api', 'both'],
            default='csv',
            help='Ingestion source: csv, api, or both (default: csv)'
        )

    def handle(self, *args, **options):
        chunk_size = options['chunk_size']
        source = options['source']
        
        if source in ['csv', 'both']:
            self.stdout.write(self.style.WARNING(f"Initializing CSV ETL Pipeline (chunk_size={chunk_size})..."))
            try:
                pipeline = CSVETLPipeline(chunk_size=chunk_size)
                pipeline.run()
                self.stdout.write(self.style.SUCCESS("CSV ETL Pipeline execution completed successfully!"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"CSV ETL Pipeline execution failed: {e}"))
                if source == 'both':
                    raise e
        
        if source in ['api', 'both']:
            self.stdout.write(self.style.WARNING("Initializing Adzuna API Daily Ingestion..."))
            try:
                run_adzuna_ingestion()
                self.stdout.write(self.style.SUCCESS("Adzuna API Ingestion execution completed successfully!"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Adzuna API Ingestion execution failed: {e}"))
