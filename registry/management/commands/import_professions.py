import csv
from django.core.management.base import BaseCommand, CommandError
from registry.models import Profession

class Command(BaseCommand):
    help = 'Import professions from zanimanja.csv'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to zanimanja.csv')

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        try:
            with open(csv_file, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                created = 0
                updated = 0
                for row in reader:
                    code = row.get('Sifra', '').strip()
                    name = row.get('Naziv_zanimanja', '').strip()

                    if not code or not name:
                        self.stdout.write(self.style.WARNING(f"Skipping row: {row}"))
                        continue

                    obj, is_created = Profession.objects.update_or_create(
                        code=code,
                        defaults={'name': name}
                    )

                    if is_created:
                        created += 1
                    else:
                        updated += 1

                self.stdout.write(self.style.SUCCESS(
                    f"Imported professions: {created} created, {updated} updated."
                ))

        except FileNotFoundError:
            raise CommandError(f"File {csv_file} does not exist")
