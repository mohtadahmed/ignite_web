from django.db import models

# Create your models here.
class Semester(models.Model):
    SEMESTER_CHOICES = [
        ('1-1', 'Year 1, Semester 1'),
        ('1-2', 'Year 1, Semester 2'),
        ('2-1', 'Year 2, Semester 1'),
        ('2-2', 'Year 2, Semester 2'),
        ('3-1', 'Year 3, Semester 1'),
        ('3-2', 'Year 3, Semester 2'),
        ('4-1', 'Year 4, Semester 1'),
        ('4-2', 'Year 4, Semester 2'),
    ]
    name = models.CharField(max_length=10, choices=SEMESTER_CHOICES, unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    credit = models.DecimalField(max_digits=4, decimal_places=2, default=3.00)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"