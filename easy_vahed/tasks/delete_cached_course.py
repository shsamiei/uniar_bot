from celery import shared_task
from easy_vahed.services import CacheService
from prof.models import Student


@shared_task(ignore_result=True)
def delete_all_non_used_cached_course():
    service = CacheService()

    for student in Student.objects.all():
        service.delete_non_used_courses(student.user_id)



