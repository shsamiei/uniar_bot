from django.core.management.base import BaseCommand
from prof.models import Major, University
from easy_vahed.models import Course
from easy_vahed.services import ConflictService


class Command(BaseCommand):
    help = 'This command preprocesses conflicts!'

    def handle(self, *args, **options):
        major = Major.objects.get(name='cs')
        university = University.objects.get(name='aut')

        courses = Course.objects.filter(university=university,
                                        majors__in=[major])
        service = ConflictService()
        service.preprocess_conflicts(courses)
