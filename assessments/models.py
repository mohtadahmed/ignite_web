from django.db import models
from django.utils import timezone
from accounts.models import *

# Create your models here.
class CTMark(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='ct_marks')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='ct_marks')
    title = models.CharField(max_length=100)  # e.g., CT1, CT2, Midterm
    mark = models.FloatField()
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"CT: {self.title} - {self.student.student_id} - {self.course.course_code}"


class AssignmentMark(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='assignment_marks')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignment_marks')
    title = models.CharField(max_length=100)  # e.g., Assignment 1
    mark = models.FloatField()
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Assignment: {self.title} - {self.student.student_id} - {self.course.course_code}"


class QuizMark(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='quiz_marks')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quiz_marks')
    title = models.CharField(max_length=100)  # e.g., Quiz 1
    mark = models.FloatField()
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Quiz: {self.title} - {self.student.student_id} - {self.course.course_code}"
    

class FinalExamMarkSetup(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    total_marks = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class FinalExamMark(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    marks_obtained = models.FloatField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    setup = models.ForeignKey(FinalExamMarkSetup, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')
