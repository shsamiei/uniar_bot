from django.core.management.base import BaseCommand
from easy_vahed.models import WeekDay


class Command(BaseCommand):
    help = 'This command helps you create weekdays easily!'

    def handle(self, *args, **options):
        weekdays = []
        for i in range(0, 7):
            weekdays.append(WeekDay(day=i))

        WeekDay.objects.bulk_create(weekdays)
        self.stdout.write('Weekdays created!')
