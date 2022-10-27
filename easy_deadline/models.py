from django.db import models


class Exersice(models.Model):
    name = models.CharField(max_length=255)
    course = models.ForeignKey(to='easy_vahed.Course', on_delete=models.CASCADE)
    student = models.ForeignKey(to='prof.Student', on_delete=models.CASCADE)
    deadline = models.DateTimeField()
    has_reminder = models.BooleanField(default=False)
