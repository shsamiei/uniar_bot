from django.db import models
from _helpers import english_day_mapping, persian_day_mapping


class WeekDay(models.Model):
    day = models.IntegerField()

    @property
    def english_day(self):
        return english_day_mapping[self.day]

    @property
    def persian_day(self):
        return persian_day_mapping[self.day]

    def __str__(self):
        return self.english_day


class Chart(models.Model):
    major = models.ForeignKey(to='prof.Major', on_delete=models.CASCADE)
    university = models.ForeignKey(to='prof.University', on_delete=models.CASCADE)
    file = models.FileField(upload_to='charts')


class Course(models.Model):
    name = models.CharField(max_length=255)
    professor = models.ForeignKey(to='prof.Professor', on_delete=models.CASCADE)
    university = models.ForeignKey(to='prof.University', on_delete=models.CASCADE)
    majors = models.ManyToManyField(to='prof.Major')
    weight = models.IntegerField()
    days = models.ManyToManyField(to='WeekDay')
    start_hour = models.TimeField()
    end_hour = models.TimeField()
    exam_date = models.DateField()
    exam_start = models.TimeField()
    exam_end = models.TimeField()

    def __str__(self):
        return f'{self.name} - {self.professor}'
