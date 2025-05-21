from django import forms
from .models import FinalExamMark
from accounts.models import CourseAssignment
from django.forms import modelformset_factory

class FinalExamMarkAssignmentForm(forms.Form):
    course = forms.ModelChoiceField(queryset=CourseAssignment.objects.all())
    total_marks = forms.IntegerField(min_value=1)

class FinalExamMarkForm(forms.ModelForm):
    class Meta:
        model = FinalExamMark
        fields = ['student', 'course', 'marks_obtained']

FinalExamMarkFormSet = modelformset_factory(FinalExamMark, form=FinalExamMarkForm, extra=0)
