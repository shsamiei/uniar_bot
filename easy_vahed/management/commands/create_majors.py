from django.core.management.base import BaseCommand
from prof.enums import MajorChoices
from prof.models import Major


class Command(BaseCommand):
    help = 'This command create majors!'

    def handle(self, *args, **options):
        majors = []
        for major in MajorChoices.names:
            majors.append(Major(name=major))

        Major.objects.bulk_create(majors)
        self.stdout.write('Majors created!')
