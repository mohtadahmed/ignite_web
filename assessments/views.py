from django.shortcuts import render, redirect
from .models import *
from .forms import *
from django.contrib import messages
from accounts.models import CourseAssignment


# Create your views here.
def add_ct_marks(request):
    if request.method == 'POST':
        titles = request.POST.getlist('ct_title[]')
        marks = request.POST.getlist('ct_marks[]')
        for title, mark in zip(titles, marks):
            # Save each CT mark
            pass
        return redirect('ct_marks_list')
    return render(request, 'assessments/add_ct_marks.html')

def add_assignment_marks(request):
    if request.method == 'POST':
        titles = request.POST.getlist('assignment_title[]')
        marks = request.POST.getlist('assignment_marks[]')
        for title, mark in zip(titles, marks):
            # Save each Assignment mark
            pass
        return redirect('assignment_marks_list')
    return render(request, 'assessments/add_assignment_marks.html')

def add_quiz_marks(request):
    if request.method == 'POST':
        title = request.POST.get('quiz_title')
        mark = request.POST.get('quiz_marks')
        # Save quiz mark
        return redirect('quiz_marks_list')
    return render(request, 'assessments/add_quiz_marks.html')


def ct_marks_list(request):
    ct_marks = CTMark.objects.select_related('student', 'course').all()
    return render(request, 'assessments/ct_marks_list.html', {'ct_marks': ct_marks})

def assignment_marks_list(request):
    assignment_marks = AssignmentMark.objects.select_related('student', 'course').all()
    return render(request, 'assessments/assignment_marks_list.html', {'assignment_marks': assignment_marks})

def quiz_marks_list(request):
    quiz_marks = QuizMark.objects.select_related('student', 'course').all()
    return render(request, 'assessments/quiz_marks_list.html', {'quiz_marks': quiz_marks})


def marks_view(request):
    ct_marks = CTMark.objects.select_related('student', 'course')
    assignment_marks = AssignmentMark.objects.select_related('student', 'course')
    quiz_marks = QuizMark.objects.select_related('student', 'course')

    return render(request, 'marks/marks_panel.html', {
        'ct_marks': ct_marks,
        'assignment_marks': assignment_marks,
        'quiz_marks': quiz_marks,
    })


def assign_final_exam_marks(request):
    if request.method == 'POST':
        form = FinalExamMarkAssignmentForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data['course']
            total_marks = form.cleaned_data['total_marks']
            course.final_exam_marks = total_marks
            course.save()
            messages.success(request, "Final exam marks assigned.")
            return redirect('assigned_courses_list')
    else:
        form = FinalExamMarkAssignmentForm()
    return render(request, 'marks/assign_final_exam_marks.html', {'form': form})


def add_final_exam_marks(request, course_id):
    course = CourseAssignment.objects.get(id=course_id)
    students = StudentProfile.objects.filter(enrolled_courses=course.course)

    if request.method == 'POST':
        formset = FinalExamMarkFormSet(request.POST, queryset=FinalExamMark.objects.filter(course=course))
        if formset.is_valid():
            formset.save()
            messages.success(request, "Final exam marks submitted.")
            return redirect('faculty_dashboard')
    else:
        # Prepopulate for all students in the course
        initial_data = [
            {'student': student, 'course': course}
            for student in students
        ]
        formset = FinalExamMarkFormSet(queryset=FinalExamMark.objects.none(), initial=initial_data)

    return render(request, 'faculty/add_final_exam_marks.html', {'formset': formset, 'course': course})
