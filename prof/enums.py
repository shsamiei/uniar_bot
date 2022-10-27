from django.db import models


class UniversityChoices(models.TextChoices):
    aut = 'aut', 'امیرکبیر'
    sut = 'sut', 'شریف'
    ut = 'ut', 'تهران'


class MajorChoices(models.TextChoices):
    cs = 'cs', 'علوم کامپیوتر'
    ce = 'ce', 'مهندسی کامپیوتر'
    math = 'math', 'ریاضیات و کاربردها'
    electric = 'electric', 'برق'
    mechanic = 'mechanic', 'مکانیک'
    civil = 'civil', 'عمران'
    aerospace = 'aerospace', 'هوافضا'


class YearChoices(models.TextChoices):
    y_98 = '98', 'ورودی 98'
    y_99 = '99', 'ورودی 99'
    y_00 = '00', 'ورودی 1400'
    y_01 = '01', 'ورودی 1401'
