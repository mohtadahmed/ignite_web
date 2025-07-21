from django.db import models
from django.utils import timezone
from accounts.models import User, Course, StudentProfile
from academics.models import Semester

# Create your models here.
class CTMark(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='ct_marks')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='ct_marks')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=100)  # e.g., CT1, CT2, Midterm
    mark = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ['student', 'course', 'semester']

    def __str__(self):
        return f"CT: {self.title} - {self.student.student_id} - {self.course.course_code}"


class AssignmentMark(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='assignment_marks')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignment_marks')
    title = models.CharField(max_length=100)  # e.g., Assignment 1
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, null=True, blank=True)
    mark = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ['student', 'course', 'semester']

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


class CourseMark(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, null=True, blank=True)

    attendance_mark = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    ct_mark = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    final_exam_mark = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_mark = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    letter_grade = models.CharField(max_length=2, blank=True, null=True)
    grade_point = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.student} - {self.course} - Semester {self.semester}"

    class Meta:
        unique_together = ('student', 'course', 'semester')


class SemesterResult(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, null=True, blank=True)
    gpa = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        unique_together = ('student', 'semester')

    def __str__(self):
        return f"{self.student} - Semester {self.semester} GPA: {self.gpa}"

class CGPARecord(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    total_credits = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.student} - CGPA: {self.cgpa}"