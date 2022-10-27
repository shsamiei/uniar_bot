from django.contrib import admin
from .models import University, Student, Professor, Major


admin.site.register(University)
admin.site.register(Student)
admin.site.register(Professor)
admin.site.register(Major)
