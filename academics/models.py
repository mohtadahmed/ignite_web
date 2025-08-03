from django.db import models
from accounts.models import User, Course
from django.utils import timezone

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


class Routine(models.Model):
    file = models.FileField(upload_to='static/uploads/routine/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
    

class CourseResource(models.Model):
    CATEGORY_CHOICES = [
        ('lecture', 'Lecture Slide / Material'),
        ('book', 'Book / Reference'),
        ('note', 'Note'),
        ('question', 'Question Paper / Practice'),
        ('link', 'Link'),
        ('other', 'Other'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='uploads/resources/', blank=True, null=True)
    external_link = models.URLField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

class ScheduleItem(models.Model):
    EXAM_TYPES = [
        ('CT', 'Class Test'),
        ('ASSIGNMENT', 'Assignment'),
        ('QUIZ', 'Quiz'),
        ('LAB', 'Lab Exam'),
        ('VIVA', 'Viva'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    scheduled_date = models.DateTimeField()
    faculty = models.ForeignKey(User, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_overdue(self):
        return timezone.now() > self.scheduled_date

    def days_left(self):
        delta = self.scheduled_date - timezone.now()
        return delta.days

    def __str__(self):
        return f"{self.course.name} - {self.exam_type}"