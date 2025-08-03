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


# def add_final_exam_marks(request, course_id):
#     course = CourseAssignment.objects.get(id=course_id)
#     students = StudentProfile.objects.filter(enrolled_courses=course.course)

#     if request.method == 'POST':
#         formset = FinalExamMarkFormSet(request.POST, queryset=FinalExamMark.objects.filter(course=course))
#         if formset.is_valid():
#             formset.save()
#             messages.success(request, "Final exam marks submitted.")
#             return redirect('faculty_dashboard')
#     else:
#         # Prepopulate for all students in the course
#         initial_data = [
#             {'student': student, 'course': course}
#             for student in students
#         ]
#         formset = FinalExamMarkFormSet(queryset=FinalExamMark.objects.none(), initial=initial_data)

#     return render(request, 'faculty/add_final_exam_marks.html', {'formset': formset, 'course': course})


# Attendance Mark Section
def attendance_mark_entry(request):
    semesters = Semester.objects.all()
    return render(request, 'marks/attendance_entry.html', {'semesters': semesters})


def get_courses_by_semester(request):
    semester_id = request.GET.get('semester_id') 
    print('semester_id', semester_id)
    courses = Course.objects.filter(semester_id=semester_id).values('id', 'course_code', 'course_name', 'credit')
    print('courses', courses)
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


def add_final_exam_mark(request):
    if request.method == 'POST':
        print('POST request received', request.POST)
        semester_id = request.POST.get('semester')
        course_id = request.POST.get('course')
        student_ids = request.POST.getlist('student_ids')

        if not all([semester_id, course_id, student_ids]):
            messages.error(request, "Semester, course, and student list are required.")
            print('Error: Missing semester/course/student_ids')
            return redirect('add_final_exam_mark')

        for student_id in student_ids:
            mark = request.POST.get(f'marks_{student_id}')
            if mark is not None and mark != '':
                FinalExamMark.objects.update_or_create(
                    student_id=student_id,
                    course_id=course_id,
                    semester_id=semester_id,
                    defaults={
                        'marks_obtained': mark,
                        'created_by': request.user,
                        'created_at': timezone.now()
                    }
                )
                print(f'Mark saved for student {student_id}: {mark}')
            else:
                print(f'Skipped student {student_id}: no mark entered')

        messages.success(request, "Final exam marks saved successfully.")
        return redirect('add_final_exam_mark')

    context = {
        'semesters': Semester.objects.all(),
        'courses': Course.objects.all(),
        'students': StudentProfile.objects.all()
    }
    return render(request, 'marks/final_exam_marks_add.html', context)


def get_students_by_course(request):
    semester_id = request.GET.get('semester_id')
    course_id = request.GET.get('course_id')
    students = StudentProfile.objects.filter(semester_id=semester_id).values('id', 'student_id')
    return JsonResponse({'students': list(students)})


from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING
from assessments.utils import calculate_grade

def final_result_panel(request):
    semesters = Semester.objects.all()
    courses = Course.objects.all()
    results = []

    selected_semester_id = request.GET.get('semester')
    selected_course_id = request.GET.get('course')

    if selected_semester_id and selected_course_id:
        selected_semester = Semester.objects.get(id=selected_semester_id)
        selected_course = Course.objects.get(id=selected_course_id)

        try:
            distribution = MarkDistribution.objects.get(course=selected_course)
        except MarkDistribution.DoesNotExist:
            messages.error(request, f"Mark distribution not found for course: {selected_course.course_name}")
            return render(request, 'marks/final_result_panel.html', {
                'semesters': semesters,
                'courses': courses,
                'selected_semester_id': int(selected_semester_id),
                'selected_course_id': int(selected_course_id),
                'results': [],
            })

        ct_marks = CTMark.objects.filter(course=selected_course, student__semester=selected_semester)
        attendance_marks = AttendanceMark.objects.filter(course=selected_course, student__semester=selected_semester)
        final_exam_marks = FinalExamMark.objects.filter(course=selected_course, student__semester=selected_semester)

        students = StudentProfile.objects.filter(semester=selected_semester)

        for student in students:
            ct = ct_marks.filter(student=student).first()
            attendance = attendance_marks.filter(student=student).first()
            final = final_exam_marks.filter(student=student).first()

            # Default to 0 if mark is missing
            ct_score = ct.mark if ct else 0
            attendance_score = attendance.mark if attendance else 0
            final_score = final.marks_obtained if final else 0

            # Compute total score
            total_score = (
                Decimal(ct_score) * Decimal(distribution.ct_weight) / Decimal(100) +
                Decimal(attendance_score) * Decimal(distribution.attendance_weight) / Decimal(100) +
                Decimal(final_score) * Decimal(distribution.final_exam_weight) / Decimal(100)
            )

            # Calculate max total marks based on course credit
            total_marks_by_credit = {4: 100, 3: 75, 2: 50, 1: 25}
            max_marks = total_marks_by_credit.get(selected_course.credit, 100)

            percentage = float(total_score) / max_marks * 100
            grade, grade_point = calculate_grade(percentage)

            results.append({
                'student': student,
                'ct': ct_score,
                'attendance': attendance_score,
                'final': final_score,
                'total': round(total_score, 2),
                'percentage': round(percentage, 2),
                'grade': grade,
                'grade_point': grade_point
            })
    print('results', results)

    return render(request, 'marks/final_result_panel.html', {
        'semesters': semesters,
        'courses': courses,
        'selected_semester_id': int(selected_semester_id) if selected_semester_id else None,
        'selected_course_id': int(selected_course_id) if selected_course_id else None,
        'results': results,
    })


def set_mark_distribution(request):
    courses = Course.objects.all()

    if request.method == 'POST':
        print('POST request received for mark distribution', request.POST)
        course_id = request.POST.get('course')
        ct_weight = float(request.POST.get('ct_weight', 0))
        attendance_weight = float(request.POST.get('attendance_weight', 0))
        final_exam_weight = float(request.POST.get('final_exam_weight', 0))

        total = ct_weight + attendance_weight + final_exam_weight
        if total != 100:
            messages.error(request, 'Total weight must be 100%.')
            return redirect('set_mark_distribution')

        course = Course.objects.get(id=course_id)

        # Create or update distribution
        distribution, created = MarkDistribution.objects.get_or_create(
            course=course,
            defaults={
                'ct_weight': ct_weight,
                'attendance_weight': attendance_weight,
                'final_exam_weight': final_exam_weight
            }
        )

        if not created:
            # If already exists, update it
            distribution.ct_weight = ct_weight
            distribution.attendance_weight = attendance_weight
            distribution.final_exam_weight = final_exam_weight
            distribution.save()


        messages.success(request, f'Mark distribution for "{course.course_name}" saved successfully!')
        print(f'Mark distribution for course {course.course_name} saved successfully!')
        return redirect('set_mark_distribution')

    context = {
        'courses': courses,
    }
    return render(request, 'marks/set_mark_distribution.html', context)



def student_marksheet_view(request):
    students = StudentProfile.objects.all().order_by('student_id')
    selected_student = None
    marksheet = []
    ct_headers = set()
    assignment_headers = set()

    if request.method == "GET" and request.GET.get('student_id'):
        student_id = request.GET.get('student_id')
        selected_student = get_object_or_404(StudentProfile, id=student_id)

        # courses = Course.objects.filter(student=selected_student).distinct()
        course_ids = set()

        # Extract course IDs from each mark model
        course_ids.update(CTMark.objects.filter(student=selected_student).values_list('course_id', flat=True))
        course_ids.update(AssignmentMark.objects.filter(student=selected_student).values_list('course_id', flat=True))
        course_ids.update(QuizMark.objects.filter(student=selected_student).values_list('course_id', flat=True))
        course_ids.update(FinalExamMark.objects.filter(student=selected_student).values_list('course_id', flat=True))
        course_ids.update(LabMark.objects.filter(student=selected_student).values_list('course_id', flat=True))
        course_ids.update(ThesisMark.objects.filter(student=selected_student).values_list('course_id', flat=True))
        course_ids.update(FieldWorkMark.objects.filter(student=selected_student).values_list('course_id', flat=True))


        # Now get the Course objects
        courses = Course.objects.filter(id__in=course_ids)

        
        for course in courses:
            row = {
                'course': course,
                'ct_marks': [],
                'assignment_marks': [],
                'quiz': '-',
                'attendance': '-',
                'final': '-',
                'lab': None,
                'thesis': None,
                'field_work': None,
                'total': 0
            }

            # ct_marks = CTMark.objects.filter(student=selected_student, course=course).order_by('id')
            # print('ct_marks', ct_marks)
            # for idx, ct in enumerate(ct_marks, 1):
            #     row['ct_marks'].append(ct.mark)
            #     ct_headers.add(f'CT{idx}')
            #     row['total'] += ct.mark
            # print('ct_headers', ct_headers)
            row['ct_marks'] = []  # Make sure it's a flat list
            ct_marks = CTMark.objects.filter(student=selected_student, course=course).order_by('id')

            for idx, ct in enumerate(ct_marks, 1):
                row['ct_marks'].append(float(ct.mark))  # Convert Decimal to float or str if needed
                ct_headers.add(f'CT{idx}')
                row['total'] += ct.mark


            assignment_marks = AssignmentMark.objects.filter(student=selected_student, course=course).order_by('id')
            for idx, a in enumerate(assignment_marks, 1):
                row['assignment_marks'].append(a.mark)
                assignment_headers.add(f'Assignment{idx}')
                row['total'] += a.mark

            attendance = AttendanceMark.objects.filter(student=selected_student, course=course).first()
            if attendance:
                row['attendance'] = attendance.mark
                row['total'] += attendance.mark

            quiz = QuizMark.objects.filter(student=selected_student, course=course).first()
            if quiz:
                row['quiz'] = quiz.mark
                row['total'] += quiz.mark

            final = FinalExamMark.objects.filter(student=selected_student, course=course).first()
            if final:
                row['final'] = final.marks_obtained
                row['total'] += Decimal(str(final.marks_obtained))

            lab = LabMark.objects.filter(student=selected_student, course=course).first()
            if lab:
                row['lab'] = lab
                row['total'] += Decimal(str(lab.quiz_viva)) + Decimal(str(lab.experiment)) + Decimal(str(lab.attendance))

            thesis = ThesisMark.objects.filter(student=selected_student, course=course).first()
            if thesis:
                row['thesis'] = thesis
                row['total'] += thesis.total_mark

            field = FieldWorkMark.objects.filter(student=selected_student, course=course).first()
            if field:
                row['field_work'] = field
                row['total'] += field.mark

            marksheet.append(row)

    return render(request, 'marks/student_marksheet.html', {
        'students': students,
        'selected_student': selected_student,
        'marksheet': marksheet,
        'ct_headers': sorted(ct_headers),
        'assignment_headers': sorted(assignment_headers),
    })


# Generate marksheet as pdf

from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.db.models import Sum


def generate_marksheet(request):
    students = StudentProfile.objects.all()
    semesters = Semester.objects.all()

    selected_student_id = request.GET.get('student')
    selected_semester = request.GET.get('semester')

    context = {
        'students': students,
        'semesters': semesters,
    }

    if selected_student_id and selected_semester:
        student = StudentProfile.objects.get(id=selected_student_id)
        courses = Course.objects.filter(semester=selected_semester)
        result_data = []
        total_credits = 0
        total_grade_points = Decimal(0)

        for course in courses:
            try:
                course_type = course.course_type.lower()
                credit = course.credit
                total_mark = Decimal(0)

                if course_type == 'theory':
                    ct_marks = CTMark.objects.filter(student=student, course=course).aggregate(
                        total=Sum('mark')
                    )['total'] or 0
                    ct_avg = (Decimal(ct_marks) / 3).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if ct_marks else Decimal(0)
                    print('ct_avg', ct_avg)
                    attendance = AttendanceMark.objects.filter(student=student, course=course).first()
                    print('attendance', attendance)
                    attendance_mark = Decimal(attendance.mark).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if attendance else Decimal(0)
                    print('attendance_mark', attendance_mark)
                    final_exam = Decimal(FinalExamMark.objects.get(student=student, course=course).marks_obtained).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if FinalExamMark.objects.filter(student=student, course=course).exists() else Decimal(0)
                    print('final_exam', final_exam)

                    total_mark = (
                        (Decimal(ct_avg) +
                        (Decimal(attendance_mark)  +
                        (Decimal(final_exam) )))
                    ).quantize(Decimal('0.01'), rounding=ROUND_CEILING)
                    print('total_mark', total_mark)

                elif course_type == 'lab':
                    lab_mark = LabMark.objects.get(student=student, course=course)
                    total_mark = (
                        Decimal(lab_mark.quiz_viva).quantize(Decimal('0.01'), rounding=ROUND_CEILING) +
                        Decimal(lab_mark.experiment).quantize(Decimal('0.01'), rounding=ROUND_CEILING) +
                        Decimal(lab_mark.attendance).quantize(Decimal('0.01'), rounding=ROUND_CEILING)
                    ).quantize(Decimal('0.01'), rounding=ROUND_CEILING)
                    print('lab total_mark', total_mark)

                elif course_type == 'thesis':
                    thesis_mark = ThesisMark.objects.get(student=student, course=course)
                    total_mark = (
                        Decimal(thesis_mark.internal).quantize(Decimal('0.01'), rounding=ROUND_CEILING) +
                        Decimal(thesis_mark.external).quantize(Decimal('0.01'), rounding=ROUND_CEILING) +
                        Decimal(thesis_mark.presentation).quantize(Decimal('0.01'), rounding=ROUND_CEILING)
                    ).quantize(Decimal('0.01'), rounding=ROUND_CEILING)
                    print('thesis total_mark', total_mark)

                elif course_type == 'field work':
                    field_work = FieldWorkMark.objects.get(student=student, course=course)
                    total_mark = Decimal(field_work.field_mark).quantize(Decimal('0.01'), rounding=ROUND_CEILING)
                    print('field_work total_mark', total_mark)

                else:
                    continue  # skip if unknown course_type

                # Normalize based on credit
                max_total = credit * 25
                percentage = (total_mark / max_total) * 100
                grade, point = calculate_grade(percentage)

                result_data.append({
                    'course': course,
                    'credit': credit,
                    'total_mark': total_mark.quantize(Decimal('0.01'), rounding=ROUND_CEILING),
                    'percentage': round(percentage, 2),
                    'grade': grade,
                    'point': point,
                })

                total_credits += credit
                total_grade_points += Decimal(point).quantize(Decimal('0.01'), rounding=ROUND_CEILING) * Decimal(credit)

            except Exception as e:
                print(f"Error processing course {course.course_name}: {e}")
                continue

        print('result_data', result_data)

        # gpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0.0
        gpa = (total_grade_points / Decimal(total_credits)).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if total_credits > 0 else Decimal('0.00')
        print('gpa', gpa)

        context.update({
            'result_data': result_data,
            'student': student,
            'selected_semester': selected_semester,
            'gpa': gpa,
        })

        if 'export_pdf' in request.GET:
            html = render_to_string('marks/marksheet_pdf.html', context)
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=Marksheet_{student.student_id}_{selected_semester}.pdf'
            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('PDF generation error')
            return response

    return render(request, 'marks/marksheet_panel.html', context)


from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib import colors
from reportlab.lib.units import mm, inch
from io import BytesIO
from reportlab.pdfgen import canvas


def generate_marksheet_pdf(request, student_id, semester_id):
    try:
        # Reuse your existing calculation logic
        student = StudentProfile.objects.get(id=student_id)
        semester = Semester.objects.get(id=semester_id)
        courses = Course.objects.filter(semester=semester)
        
        # Prepare result data (same as your HTML version)
        result_data = []
        total_credits = 0
        total_grade_points = Decimal(0)
        
        for course in courses:
            try:
                course_type = course.course_type.lower()
                credit = course.credit
                total_mark = Decimal(0)

                if course_type == 'theory':
                    ct_marks = CTMark.objects.filter(student=student, course=course).aggregate(total=Sum('mark'))['total'] or 0
                    ct_avg = (Decimal(ct_marks) / 3).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if ct_marks else Decimal(0)
                    
                    attendance = AttendanceMark.objects.filter(student=student, course=course).first()
                    attendance_mark = Decimal(attendance.mark).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if attendance else Decimal(0)
                    
                    final_exam = Decimal(FinalExamMark.objects.get(
                        student=student, 
                        course=course
                    ).marks_obtained).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

                    total_mark = (ct_avg + attendance_mark + final_exam).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

                elif course_type == 'lab':
                    lab_mark = LabMark.objects.get(student=student, course=course)
                    total_mark = (
                        Decimal(lab_mark.quiz_viva) +
                        Decimal(lab_mark.experiment) + 
                        Decimal(lab_mark.attendance)
                    ).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

                elif course_type == 'thesis':
                    thesis_mark = ThesisMark.objects.get(student=student, course=course)
                    total_mark = (
                        Decimal(thesis_mark.internal) +
                        Decimal(thesis_mark.external) +
                        Decimal(thesis_mark.presentation)
                    ).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

                elif course_type == 'field work':
                    field_work = FieldWorkMark.objects.get(student=student, course=course)
                    total_mark = Decimal(field_work.field_mark).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

                else:
                    continue

                # Grade calculation (same as your existing logic)
                max_total = credit * 25
                percentage = (total_mark / max_total) * 100
                grade, point = calculate_grade(float(percentage))
                
                result_data.append({
                    'course': course,
                    'credit': credit,
                    'total_mark': total_mark,
                    'percentage': percentage,
                    'grade': grade,
                    'point': Decimal(point).quantize(Decimal('0.01'), rounding=ROUND_CEILING),
                })

                total_credits += credit
                total_grade_points += Decimal(point) * Decimal(credit)

            except Exception as e:
                print(f"Skipping course {course.course_name}: {str(e)}")
                continue

        # PDF Generation
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=30, leftMargin=30,
                            topMargin=20, bottomMargin=20)
        
        # Custom styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            'CenterTitle',
            parent=styles['Title'],
            alignment=1,
            fontSize=14,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            'CenterNormal',
            parent=styles['Normal'],
            alignment=1,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            'FooterItalic',
            parent=styles['Italic'],
            alignment=1,
            fontSize=9
        ))
        styles.add(ParagraphStyle(
            'BottomFooter',
            parent=styles['Italic'],
            alignment=1,  # CENTER
            fontSize=9,
            textColor=colors.grey,
            spaceBefore=12  # Add some space above the footer
        ))
        

        story = []

        # Add University Logo
        logo_path = "static/img/university_logo.png"  # Update with your actual path
        logo = Image(logo_path, width=1.5*inch, height=1.5*inch)
        logo.hAlign = 'CENTER'
        story.append(logo)
        story.append(Spacer(1, 12))  # Add some space after logo
        
        # Header
        story.append(Paragraph("UNIVERSITY OF CHITTAGONG", styles['CenterTitle']))
        story.append(Paragraph("CHITTAGONG, BANGLADESH", styles['CenterNormal']))
        story.append(Spacer(1, 6))

        story.append(Paragraph("Department of Electrical and Electronic Engineering", styles['CenterTitle']))
        story.append(Paragraph(f"{semester.name} B.Sc. Engineering Examination", styles['CenterNormal']))
        story.append(Paragraph("Held in April - May, 2018 (Regular)", styles['CenterNormal']))
        story.append(Spacer(1, 12))
        
        # Student Info
        story.append(Paragraph("Grade Sheet", styles['CenterTitle']))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"Student ID : {student.student_id}", styles['CenterNormal']))
        story.append(Paragraph(f"Name of the Student: Dummy Student Name", styles['CenterNormal']))
        story.append(Paragraph(f"Name of the Hall : Dummy hall name", styles['CenterNormal']))
        story.append(Paragraph(f"Session : {student.session}", styles['CenterNormal']))
        story.append(Spacer(1, 12))
        
        # Grade Table
        table_data = [
            ["Course Code", "Course Title", "Credit", "Letter Grade", "Grade Point"]
        ]
        
        for item in result_data:
            table_data.append([
                item['course'].course_code,
                item['course'].course_name,
                str(item['credit']),
                item['grade'],
                f"{item['point']:.2f}"
            ])
        
        table = Table(table_data, colWidths=[1.2*inch, 3*inch, 0.7*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 1, colors.grey),
            ('LINEBELOW', (0,0), (-1,0), 1, colors.grey),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))
        
        # Footer
        gpa = (total_grade_points / Decimal(total_credits)).quantize(Decimal('0.01'), rounding=ROUND_CEILING)
        # story.append(Paragraph(f"GPA: {gpa:.2f}", styles['normal']))
        # story.append(Spacer(1, 24))
        # Four items side by side
        footer_data = [
            [f"Total Credits Offered : {total_credits:.2f}", 
             f"Total Credits Earned : {total_credits:.2f}",
             f"GPA: {gpa:.2f}",
             "Result: P"]
        ]

        footer_table = Table(footer_data, colWidths=[2*inch, 2*inch, 1.5*inch, 1.5*inch])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
        ]))
        story.append(footer_table)
        story.append(Spacer(1, 6))
        story.append(Paragraph("Remarks:", styles['CenterNormal']))
        story.append(Spacer(1, 12))
        
        # Signature lines side by side
        signature_data = [
            ["Date of Publication:..................", "Prepared By:....................."],
            ["Date of Issue:........................", "Compared By:......................"]
        ]
        
        signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
        ]))
        story.append(signature_table)
        story.append(Spacer(1, 12))
        
        # Software footer (centered)
        story.append(Spacer(1, 48))
        story.append(Paragraph("<font color=#808080>Ignite Software Generated Marksheet</font>", styles['FooterItalic']))
        story.append(Paragraph("<font color=#808080>Ignite: Result Management Software</font>", styles['FooterItalic']))

        # Ensure everything fits on one page
        content = KeepTogether(story)

        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Marksheet_{student.student_id}_{semester.name}.pdf"'
        return response
        
    except Exception as e:
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)



from datetime import datetime

# Transcript Section
import os
from io import BytesIO
from datetime import datetime  # Added missing import
from decimal import Decimal, ROUND_CEILING
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from django.db.models import Sum
from PIL import Image  # For image handling

def transcript_view(request):
    students = StudentProfile.objects.all()
    selected_student_id = request.GET.get('student_id')
    transcript_data = []
    total_credits = 0
    total_grade_points = Decimal(0)

    if selected_student_id:
        student = get_object_or_404(StudentProfile, id=selected_student_id)
        semesters = Semester.objects.all().order_by('name')

        for semester in semesters:
            semester_courses = Course.objects.filter(semester=semester)
            semester_data = []
            semester_credits = 0
            semester_grade_points = Decimal(0)

            for course in semester_courses:
                try:
                    course_type = course.course_type.lower()
                    credit = course.credit
                    total_mark = Decimal(0)

                    if course_type == 'theory':
                        ct_marks = CTMark.objects.filter(student=student, course=course).aggregate(
                            total=Sum('mark')
                        )['total'] or 0
                        ct_avg = (Decimal(ct_marks) / 3).quantize(Decimal('0.01'), rounding=ROUND_CEILING)
                        
                        attendance = AttendanceMark.objects.filter(student=student, course=course).first()
                        attendance_mark = Decimal(attendance.mark) if attendance else Decimal(0)
                        
                        final_exam = Decimal(FinalExamMark.objects.get(
                            student=student, 
                            course=course
                        ).marks_obtained) if FinalExamMark.objects.filter(
                            student=student, 
                            course=course
                        ).exists() else Decimal(0)
                        
                        total_mark = (ct_avg + attendance_mark + final_exam).quantize(Decimal('0.01'))

                    elif course_type == 'lab':
                        lab_mark = LabMark.objects.get(student=student, course=course)
                        total_mark = (
                            Decimal(lab_mark.quiz_viva) +
                            Decimal(lab_mark.experiment) +
                            Decimal(lab_mark.attendance)
                        ).quantize(Decimal('0.01'))

                    elif course_type == 'thesis':
                        thesis_mark = ThesisMark.objects.get(student=student, course=course)
                        total_mark = (
                            Decimal(thesis_mark.internal) +
                            Decimal(thesis_mark.external) +
                            Decimal(thesis_mark.presentation)
                        ).quantize(Decimal('0.01'))

                    elif course_type == 'field work':
                        field_work = FieldWorkMark.objects.get(student=student, course=course)
                        total_mark = Decimal(field_work.field_mark).quantize(Decimal('0.01'))

                    else:
                        continue

                    max_total = credit * 25
                    percentage = (total_mark / max_total) * 100
                    grade, point = calculate_grade(percentage)

                    semester_data.append({
                        'course': course,
                        'credit': credit,
                        'total_mark': total_mark,
                        'percentage': percentage.quantize(Decimal('0.01')),
                        'grade': grade,
                        'point': point,
                    })

                    semester_credits += credit
                    semester_grade_points += Decimal(point) * Decimal(credit)

                except Exception as e:
                    print(f"Error processing course {course.course_name}: {e}")
                    continue

            semester_gpa = (semester_grade_points / Decimal(semester_credits)).quantize(
                Decimal('0.01'), rounding=ROUND_CEILING) if semester_credits > 0 else Decimal('0.00')
            
            transcript_data.append({
                'semester': semester,
                'courses': semester_data,
                'gpa': semester_gpa,
                'credits': semester_credits
            })

            total_credits += semester_credits
            total_grade_points += semester_grade_points

        final_cgpa = (total_grade_points / Decimal(total_credits)).quantize(
            Decimal('0.01'), rounding=ROUND_CEILING) if total_credits > 0 else Decimal('0.00')

        if 'pdf' in request.GET:
            buffer = BytesIO()
            pdf = canvas.Canvas(buffer, pagesize=letter)
            
            # Set margins and initial positions
            left_margin = 50
            right_margin = 550
            center = 300
            y_position = 750  # Start near the top
            
            # University Header
            try:
                # Draw logos (50x50 pixels)
                if os.path.exists('static/img/university_logo.png'):
                    pdf.drawImage('static/img/university_logo.png', left_margin, y_position-50, width=50, height=50)
                if os.path.exists('static/img/department_logo.png'):
                    pdf.drawImage('static/img/department_logo.png', right_margin-50, y_position-50, width=50, height=50)
            except Exception as e:
                print(f"Error loading logos: {e}")

            # University Info (centered)
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawCentredString(center, y_position, "University of Chittagong")
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawCentredString(center, y_position-25, "Faculty of Engineering")
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawCentredString(center, y_position-45, "Department of Electrical & Electronic Engineering")
            
            # Student Info (two columns)
            y_position -= 80
            pdf.setFont("Helvetica", 12)
            pdf.drawString(left_margin, y_position, f"Name: student.full_name")
            pdf.drawString(left_margin, y_position-20, f"Student ID: {student.student_id}")
            pdf.drawString(center-50, y_position, f"Session: {getattr(student, 'session', 'N/A')}")
            pdf.drawString(center-50, y_position-20, f"Hall: {getattr(student, 'hall', 'N/A')}")
            
            # Transcript Title with line
            y_position -= 50
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawCentredString(center, y_position, "ACADEMIC TRANSCRIPT")
            pdf.line(left_margin, y_position-5, right_margin, y_position-5)
            
            y_position -= 30  # Space before first semester

            for sem in transcript_data:
                # Check for page break
                if y_position < 100:
                    pdf.showPage()
                    y_position = 750
                    pdf.setFont("Helvetica-Bold", 12)
                    pdf.drawString(left_margin, y_position, f"Continuing Transcript for student.full_name")
                    y_position -= 30

                # Semester Header
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(left_margin, y_position, f"Semester: {sem['semester'].name}")
                
                # GPA and Credits on same line
                pdf.drawString(right_margin-150, y_position, f"GPA: {sem['gpa']} | Credits: {sem['credits']}")
                y_position -= 20
                
                # Table Data
                table_data = [
                    ["Code", "Course Title", "Cr", "Total", "Grade", "Point"]
                ]
                
                for course in sem['courses']:
                    table_data.append([
                        course['course'].course_code,
                        course['course'].course_name[:35],  # Slightly longer title
                        str(course['credit']),
                        str(course['total_mark']),
                        course['grade'],
                        str(course['point']),
                    ])
                
                # Create table with optimized column widths
                col_widths = [50, 220, 30, 40, 40, 40]
                table = Table(table_data, colWidths=col_widths)
                
                # Table styling
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F8F8F8")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.black),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('ALIGN', (1,1), (1,-1), 'LEFT'),  # Left-align course titles
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,-1), 9),
                    ('BOTTOMPADDING', (0,0), (-1,0), 8),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.gray),
                    ('LEFTPADDING', (1,1), (1,-1), 4),  # Extra padding for course titles
                ]))
                
                # Draw table
                table.wrapOn(pdf, left_margin, y_position - (len(table_data) * 16))
                table.drawOn(pdf, left_margin, y_position - (len(table_data) * 16))
                y_position -= (len(table_data) * 16 + 25)  # Space after table
                
                # Add separator line between semesters
                pdf.line(left_margin, y_position+5, right_margin, y_position+5)
                y_position -= 15

            # Final CGPA
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawCentredString(center, y_position, f"Final Cumulative GPA: {final_cgpa}")
            y_position -= 30
            
            # Footer
            pdf.setFont("Helvetica-Oblique", 10)
            pdf.drawCentredString(center, y_position, "Generated by Ignite Result Management System")
            pdf.drawCentredString(center, y_position-15, f"Date: {datetime.now().strftime('%d %B %Y')}")
            
            pdf.save()
            pdf_buffer = buffer.getvalue()
            buffer.close()
            
            response = HttpResponse(pdf_buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{student.student_id}_transcript.pdf"'
            return response

        return render(request, 'marks/transcript.html', {
            'students': students,
            'selected_student_id': selected_student_id,
            'student': student,
            'transcript_data': transcript_data,
            'cgpa': final_cgpa
        })

    return render(request, 'marks/transcript.html', {'students': students})


def lab_mark_entry(request):
    students = StudentProfile.objects.all()
    courses = Course.objects.filter(course_type='lab')  # Only lab courses

    if request.method == 'POST':
        print('POST request received for lab mark entry', request.POST)
        student_id = request.POST.get('student_id')
        course_id = request.POST.get('course_id')
        quiz_viva = Decimal(request.POST.get('quiz_viva', 0))
        experiment = Decimal(request.POST.get('experiment', 0))
        attendance = Decimal(request.POST.get('attendance', 0))

        try:
            student = StudentProfile.objects.get(id=student_id)
            course = Course.objects.get(id=course_id)

            total_credit = course.credit
            total_marks = total_credit * Decimal('25')  # Assuming 25 marks per 1 credit

            max_quiz_viva = (total_marks * Decimal('0.40'))
            max_experiment = (total_marks * Decimal('0.50'))
            max_attendance = (total_marks * Decimal('0.10'))

            if quiz_viva > max_quiz_viva or experiment > max_experiment or attendance > max_attendance:
                messages.error(request, f"One or more marks exceed the maximum allowed values.")
                return redirect('lab_mark_entry')

            try:
                LabMark.objects.update_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'quiz_viva': quiz_viva,
                        'experiment': experiment,
                        'attendance': attendance
                    }
                )
                messages.success(request, "Lab mark saved successfully.")
                print("Lab mark saved successfully.")
                
                return redirect('lab_mark_entry')
            except Exception as e:
                print("Exception occurred while saving lab mark:", e)
                messages.error(request, f"Error: {e}")
        
        except Exception as e:
            print("Exception occurred while processing lab mark entry:", e)
            messages.error(request, f"Error: {e}")

    return render(request, 'marks/lab_mark_entry.html', {
        'students': students,
        'courses': courses
    })



def add_thesis_mark(request):
    students = StudentProfile.objects.all()
    thesis_courses = Course.objects.filter(course_type='thesis')
    print('thesis_courses', thesis_courses)

    if request.method == 'POST':
        print('POST request received for thesis mark entry', request.POST)
        student_id = request.POST.get('student_id')
        course_id = float(request.POST.get('course_id'))
        internal = float(request.POST.get('internal_mark'))
        external = float(request.POST.get('external_mark'))
        presentation = float(request.POST.get('presentation_mark'))

        # Calculation: 35% internal, 35% external, 30% presentation
        total = internal + external + presentation
        print('total', total)

        student = StudentProfile.objects.get(id=student_id)
        course = Course.objects.get(id=course_id)

        mark_obj, created = ThesisMark.objects.update_or_create(
            student=student,
            course=course,
            defaults={
                'internal': internal,
                'external': external,
                'presentation': presentation,
                'total_mark': total
            }
        )

        messages.success(request, 'Thesis mark saved successfully.')
        return redirect('add_thesis_mark')

    return render(request, 'marks/thesis_mark_entry.html', {
        'students': students,
        'thesis_courses': thesis_courses
    })


def field_work_mark_entry(request):
    students = StudentProfile.objects.all()
    field_work_courses = Course.objects.filter(course_type='field')  # Adjust this filter if needed

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course_id = request.POST.get('course_id')
        field_mark = request.POST.get('field_mark')

        try:
            student = StudentProfile.objects.get(id=student_id)
            course = Course.objects.get(id=course_id)

            # Calculate max allowed marks for this course
            max_total = course.credit * 25

            if float(field_mark) > max_total:
                messages.error(request, f"Field work mark exceeds the maximum allowed ({max_total}).")
            else:
                FieldWorkMark.objects.update_or_create(
                    student=student,
                    course=course,
                    defaults={'field_mark': field_mark}
                )
                messages.success(request, "Field Work Mark saved successfully.")
                return redirect('field_work_mark_entry')

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return render(request, 'marks/field_work_mark_entry.html', {
        'students': students,
        'field_work_courses': field_work_courses,
    })