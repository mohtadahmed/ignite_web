from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
    

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('faculty', 'Faculty'),
        ('student', 'Student'),
    )

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"


class StudentProfile(models.Model):
    PROGRAM_CHOICES = (
        ('B.Sc', 'B.Sc'),
        ('M.S', 'M.S'),
    )
        
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    semester = models.ForeignKey('academics.Semester', on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    session = models.CharField(max_length=10, blank=True, null=True)
    program = models.CharField(max_length=10, choices=PROGRAM_CHOICES, blank=True, null=True)
    current_semester = models.ForeignKey('academics.Semester', on_delete=models.SET_NULL, null=True, blank=True, related_name='current_students')
    migrated_semesters = models.ManyToManyField('academics.Semester', blank=True, related_name='migrated_students')

    def __str__(self):
        return f"Student: {self.user.email} - {self.student_id}"


class FacultyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, null=True)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.email} - {self.designation}, {self.department}"


class Course(models.Model):
    COURSE_TYPE_CHOICES = [
        ('theory', 'Theory'),
        ('lab', 'Lab'),
        ('field', 'Field Work'),
        ('thesis', 'Thesis'),
    ]

    course_code = models.CharField(max_length=20, unique=True)
    course_name = models.CharField(max_length=100)
    credit = models.DecimalField(max_digits=4, decimal_places=2)
    semester = models.ForeignKey('academics.Semester', on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES, default='theory')

    def __str__(self):
        return f"{self.course_code} - {self.course_name} - ({self.get_course_type_display()})"
    

class CourseAssignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    faculty = models.ForeignKey(FacultyProfile, on_delete=models.CASCADE, related_name='assignments')
    assigned_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'faculty')  # prevent duplicate assignment

    def __str__(self):
        return f"{self.course} assigned to {self.faculty}"
    

class StudentCourseEnrollment(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.student_id} enrolled in {self.course.course_code}"
