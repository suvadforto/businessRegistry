import csv
from django.core.management.base import BaseCommand
from registry.models import ActivityCode

class Command(BaseCommand):
    help = 'Load activity codes from a CSV file into ActivityCode model'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file containing activity codes'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        loaded_count = 0

        try:
            with open(csv_file, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = row['code'].strip()
                    description = row['description'].strip()

                    # Create only if it doesn't exist
                    obj, created = ActivityCode.objects.get_or_create(
                        code=code,
                        defaults={'description': description}
                    )
                    if created:
                        loaded_count += 1

            self.stdout.write(
                self.style.SUCCESS(f'Successfully loaded {loaded_count} activity code(s).')
            )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
        except KeyError:
            self.stdout.write(
                self.style.ERROR(
                    'CSV must have "code" and "description" columns'
                )
            )
