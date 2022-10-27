from django.db import models
from .enums import UniversityChoices, MajorChoices, YearChoices


class University(models.Model):
    name = models.CharField(max_length=64, choices=UniversityChoices.choices, db_index=True)

    def __str__(self):
        return self.name


class Major(models.Model):
    name = models.CharField(max_length=64, choices=MajorChoices.choices, db_index=True)

    def __str__(self):
        return self.name


class Professor(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name


class Student(models.Model):
    name = models.CharField(max_length=255, null=True)
    user_id = models.CharField(max_length=32, db_index=True)
    user_name = models.CharField(max_length=128, null=True)
    university = models.ForeignKey(to='University', on_delete=models.CASCADE)
    major = models.ForeignKey(to='Major', on_delete=models.CASCADE)
    year = models.CharField(max_length=8, choices=YearChoices.choices)
    courses = models.ManyToManyField(to='easy_vahed.Course')

    def __str__(self):
        return self.name
