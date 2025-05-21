# courses/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import CourseAssignment, Course, FacultyProfile, StudentProfile

User = get_user_model()

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'


class CourseAssignmentForm(forms.ModelForm):
    class Meta:
        model = CourseAssignment
        fields = ['course', 'faculty']

    course = forms.ModelChoiceField(queryset=Course.objects.all())
    faculty = forms.ModelChoiceField(queryset=FacultyProfile.objects.all())


class FacultyCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label='Password')

    class Meta:
        model = User
        fields = ['email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'faculty'  # assign faculty role
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            FacultyProfile.objects.create(user=user)
        return user
    

class StudentCourseEnrollmentForm(forms.Form):
    student = forms.ModelChoiceField(queryset=StudentProfile.objects.all(), label="Select Student")
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Select Courses to Assign"
    )