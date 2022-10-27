from django.core.management.base import BaseCommand
from prof.enums import UniversityChoices
from prof.models import University


class Command(BaseCommand):
    help = 'This command creates universities from enums'

    def handle(self, *args, **options):
        universities = []
        for name in UniversityChoices.names:
            universities.append(University(name=name))

        University.objects.bulk_create(universities)
        self.stdout.write('Universities created!')
