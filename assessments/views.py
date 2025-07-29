from django.shortcuts import render, redirect, get_object_or_404, redirect
from .models import *
from .forms import *
from django.contrib import messages
from accounts.models import CourseAssignment
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from django.urls import reverse


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


def add_quiz_marks(request):
    if request.method == 'POST':
        title = request.POST.get('quiz_title')
        mark = request.POST.get('quiz_marks')
        # Save quiz mark
        return redirect('quiz_marks_list')
    return render(request, 'assessments/add_quiz_marks.html')


def assignment_marks_list(request):
    assignment_marks = AssignmentMark.objects.select_related('student', 'course').all()
    return render(request, 'marks/assignment_marks_list.html', {'assignment_marks': assignment_marks})

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


# Attendance Mark Section
def attendance_mark_entry(request):
    semesters = Semester.objects.all()
    return render(request, 'marks/attendance_entry.html', {'semesters': semesters})


def get_courses_by_semester(request):
    semester_id = request.GET.get('semester_id') 
    courses = Course.objects.filter(semester_id=semester_id).values('id', 'course_code', 'course_name')
    return JsonResponse(list(courses), safe=False)


def get_students_for_attendance(request):
    semester_id = request.GET.get('semester_id')
    course_id = request.GET.get('course_id')

    students = StudentProfile.objects.filter(semester_id=semester_id)
    student_data = []

    for student in students:
        try:
            mark_obj = AttendanceMark.objects.get(
                student=student,
                course_id=course_id,
                semester_id=semester_id
            )
            mark = mark_obj.mark
        except AttendanceMark.DoesNotExist:
            mark = ''

        student_data.append({
            'id': student.id,
            'student_id': student.student_id,
            'mark': mark
        })

    return JsonResponse(student_data, safe=False)


@csrf_exempt
def save_attendance_marks(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        course_id = data.get('course_id')
        semester_id = data.get('semester_id')
        marks_data = data.get('marks')

        for item in marks_data:
            student_id = item.get('student_id')
            mark = item.get('mark')

            if mark is None or mark == '':
                mark = 0
            else:
                try:
                    mark = float(mark)
                except ValueError:
                    mark = 0

            AttendanceMark.objects.update_or_create(
                student_id=student_id,
                course_id=course_id,
                semester_id=semester_id,
                defaults={'mark': mark}
            )
        return JsonResponse({'status': 'success'})
    

# CT Marks Section
def enter_ct_marks(request):
    semesters = Semester.objects.all()
    return render(request, 'marks/add_ct_marks.html', {'semesters': semesters})


def get_ct_marks(request):
    semester_id = request.GET.get('semester_id')
    course_id = request.GET.get('course_id')

    if not semester_id or not course_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    ct_marks = CTMark.objects.filter(course_id=course_id, semester_id=semester_id)

    data = {}
    for mark in ct_marks:
        key = f"{mark.student.id}_ct{mark.title[-1]}"  # Assuming title is like 'CT1', 'CT2'
        data[key] = float(mark.mark)

    return JsonResponse({'ct_marks': data})


@csrf_exempt
def save_ct_marks(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print('data', data)

            semester_id = data.get('semester_id')
            course_id = data.get('course_id')
            marks = data.get('marks', [])

            semester = get_object_or_404(Semester, id=semester_id)
            course = get_object_or_404(Course, id=course_id)

            for entry in marks:
                student_id = entry.get('student_id')
                ct_number = entry.get('ct_number')  # e.g., 1
                mark = entry.get('mark')

                student = get_object_or_404(StudentProfile, id=student_id)
                title = f"CT{ct_number}"  # e.g., CT1, CT2

                CTMark.objects.update_or_create(
                    student=student,
                    course=course,
                    semester=semester,
                    title=title,
                    defaults={'mark': mark}
                )

            return JsonResponse({'success': True, 'redirect_url': reverse('ct_marks_list')})
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def ct_marks_list(request):
    ct_marks = CTMark.objects.select_related('student', 'course').all()
    return render(request, 'marks/ct_marks_list.html', {'ct_marks': ct_marks})


# Assignment Marks Section
def add_assignment_marks(request):
    semesters = Semester.objects.all()
    return render(request, 'marks/add_assignment_marks.html', {
        'semesters': semesters,
        'today': timezone.now().date()
    })


def get_assignment_marks(request):
    semester_id = request.GET.get('semester_id')
    course_id = request.GET.get('course_id')
    title = request.GET.get('title')

    if not (semester_id and course_id and title):
        print('missing')
        return JsonResponse({'success': False, 'message': 'Missing parameters'}, status=400)

    marks = AssignmentMark.objects.filter(
        semester_id=semester_id,
        course_id=course_id,
        title=title
    ).select_related('student') 

    data = []
    for mark in marks:
        data.append({
            'student_id': mark.student.id,
            'mark': float(mark.mark)
        })

    return JsonResponse({'success': True, 'marks': data})


def get_latest_assignment_title(request):
    semester_id = request.GET.get('semester_id')
    course_id = request.GET.get('course_id')

    if not (semester_id and course_id):
        return JsonResponse({'success': False, 'message': 'Missing semester or course ID'}, status=400)

    # Get latest assignment title used for this course+semester
    latest_assignment = AssignmentMark.objects.filter(
        semester_id=semester_id,
        course_id=course_id
    ).order_by('-id').first()

    if latest_assignment:
        return JsonResponse({'success': True, 'title': latest_assignment.title})
    else:
        return JsonResponse({'success': False, 'message': 'No assignment found'})
    


def get_assignment_titles(request):
    semester_id = request.GET.get('semester_id')
    course_id = request.GET.get('course_id')

    if not (semester_id and course_id):
        return JsonResponse({'success': False, 'message': 'Missing data'}, status=400)

    titles = AssignmentMark.objects.filter(
        semester_id=semester_id,
        course_id=course_id
    ).values_list('title', flat=True).distinct()

    return JsonResponse({'success': True, 'titles': list(titles)})


@csrf_exempt
def save_assignment_marks(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            semester_id = data.get('semester_id')
            course_id = data.get('course_id')
            title = data.get('title')
            marks_data = data.get('marks')

            semester = Semester.objects.get(id=semester_id)
            course = Course.objects.get(id=course_id)

            for item in marks_data:
                student_id = item.get('student_id')
                mark = item.get('mark')

                student = StudentProfile.objects.get(id=student_id)

                try:
                    # Try to get existing mark entry
                    assignment_mark = AssignmentMark.objects.get(
                        student=student,
                        course=course,
                        semester=semester,
                        title=title
                    )
                    # Only update the mark (not the date)
                    assignment_mark.mark = mark
                    assignment_mark.save()
                except AssignmentMark.DoesNotExist:
                    # Create new entry with date
                    AssignmentMark.objects.create(
                        student=student,
                        course=course,
                        semester=semester,
                        title=title,
                        mark=mark,
                        date=timezone.now()
                    )

            return JsonResponse({'success': True, 'message': 'Assignment marks saved successfully'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
