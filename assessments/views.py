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

def get_attendance_marks(request):
    semester_id = request.GET.get("semester_id")
    student_id = request.GET.get("student_id")

    marks = AttendanceMark.objects.select_related("student", "course", "semester").filter(
        semester_id=semester_id, student_id=student_id
    )

    data = []
    for m in marks:
        data.append({
            "semester": str(m.semester.name),
            "course": f"{m.course.course_code} - {m.course.course_name}",
            "student_id": m.student.student_id,
            "student_name": m.student.full_name,
            "mark": m.mark,
        })

    return JsonResponse(data, safe=False)


def attendance_marks_list(request):
    semesters = Semester.objects.all()
    return render(request, 'marks/attendance_marks_list.html', {'semesters': semesters})



def get_courses_by_semester(request):
    semester_id = request.GET.get('semester_id') 
    print('semester_id', semester_id)
    courses = Course.objects.filter(semester_id=semester_id).values('id', 'course_code', 'course_name', 'credit', 'course_type')
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


def get_ct_marks_new(request):
    semester_id = request.GET.get("semester_id")
    student_id = request.GET.get("student_id")

    marks = CTMark.objects.select_related("student", "course", "semester").filter(
        semester_id=semester_id, student_id=student_id
    )

    data = []
    for m in marks:
        data.append({
            "semester": str(m.semester.name),
            "course_code": m.course.course_code,
            "course_title": m.course.course_name,
            "student_id": m.student.student_id,
            "student_name": m.student.full_name,
            "title": m.title,
            "mark": m.mark,
            "date": m.date.strftime("%Y-%m-%d"),
        })

    return JsonResponse(data, safe=False)


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
    # ct_marks = CTMark.objects.select_related('student', 'course').all()
    semesters = Semester.objects.all()
    return render(request, 'marks/ct_marks_list.html', {'semesters': semesters})


def get_students_by_semester(request):
    semester_id = request.GET.get("semester_id")
    students = StudentProfile.objects.filter(semester=semester_id)
    print('students', students)

    data = [{"id": s.id, "student_id": s.student_id, "name": s.full_name} for s in students]
    return JsonResponse(data, safe=False)


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


def show_marksheet(request):
    return render(request, 'marksheet.html')



from assessments.utils import calculate_grade
from io import BytesIO
from decimal import Decimal, ROUND_CEILING
from django.http import HttpResponse

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether)
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
import os
from datetime import datetime

# -----------------------------------
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.db.models import Sum
from PIL import Image as PILImage


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
                    'point': point,
                    # 'point': Decimal(point).quantize(Decimal('0.01'), rounding=ROUND_CEILING),
                })

                total_credits += credit
                total_grade_points += Decimal(point) * Decimal(credit)

            except Exception as e:
                print(f"Skipping course {course.course_name}: {str(e)}")
                continue

        print('result_data', result_data)
        

        gpa = (total_grade_points / Decimal(total_credits)).quantize(Decimal('0.01')) if total_credits > 0 else Decimal('0.00')

        # PDF Generation
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, 
                                pagesize=letter,
                                rightMargin=30,
                                leftMargin=30,
                                topMargin=20,
                                bottomMargin=20)
        
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
        styles.add(ParagraphStyle(
            'LeftTitle',
            parent=styles['Title'],
            alignment=0,
            leftIndent=0,
            fontSize=14,
            spaceAfter=6
        ))
        styles.add(ParagraphStyle(
            'LeftNormal',
            parent=styles['Normal'],
            alignment=0,  # 0=left, 1=center, 2=right
            leftIndent=0,
            spaceAfter=6
        ))
        

        story = []

        
        logo_path = os.path.join('static', 'img', 'university_logo.png')
        if os.path.exists(logo_path):
            try:
                logo = RLImage(logo_path, width=1.5*inch, height=1.5*inch)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 12))
            except:
                story.append(Paragraph("University of Chittagong", styles['CenterTitle']))
        else:
            story.append(Paragraph("University of Chittagong", styles['CenterTitle']))
        
        # Header
        story.append(Paragraph("UNIVERSITY OF CHITTAGONG", styles['CenterTitle']))
        story.append(Paragraph("CHITTAGONG, BANGLADESH", styles['CenterNormal']))
        story.append(Spacer(1, 6))

        story.append(Paragraph("Department of Electrical and Electronic Engineering", styles['CenterTitle']))
        story.append(Paragraph(f"8th Semester B.Sc. Engineering Examination", styles['CenterNormal']))
        story.append(Paragraph("Held in May - June, 2025", styles['CenterNormal']))
        story.append(Spacer(1, 12))
        
        # Student Info
        story.append(Paragraph("Grade Sheet", styles['CenterTitle']))
        story.append(Spacer(1, 6))

        # Create a table for perfect alignment with the main content table
        student_info_data = [
            [Paragraph(f"<b>Student ID</b>:", styles['LeftNormal']), Paragraph(student.student_id, styles['LeftNormal'])],
            [Paragraph(f"<b>Name of the Student</b>:", styles['LeftNormal']), Paragraph(student.full_name, styles['LeftNormal'])],
            [Paragraph(f"<b>Name of the Hall</b>:", styles['LeftNormal']), Paragraph(student.hall, styles['LeftNormal'])],
            [Paragraph(f"<b>Session</b>:", styles['LeftNormal']), Paragraph(student.session, styles['LeftNormal'])]
        ]

        student_info_table = Table(student_info_data, colWidths=[1.5*inch, 4*inch])
        student_info_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))

        story.append(student_info_table)
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
        
        footer_data = [
            [
                Paragraph(f"<b>Total Credits Offered: {total_credits:.2f}</b>", styles['BottomFooter']),
                Paragraph(f"<b>Total Credits Earned: {total_credits:.2f}</b>", styles['BottomFooter']),
                Paragraph(f"<b>GPA: {gpa:.2f}</b>", styles['BottomFooter']),
                Paragraph(f"<b>Result: {'P' if gpa >= 2.00 else 'F'}</b>", styles['BottomFooter'])
            ]
        ]

        footer_table = Table(footer_data, colWidths=[2*inch, 2*inch, 1.5*inch, 1.5*inch])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
        ]))
        story.append(footer_table)
        story.append(Spacer(1, 6))
        story.append(Paragraph("Remarks:", styles['BottomFooter']))
        story.append(Spacer(1, 24))
        
        # Signature lines side by side
        signature_data = [
            ["Date of Publication:..........................", "Prepared By:.............................."],
            ["Date of Issue:................................", "Compared By:.............................."]
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
        story.append(Paragraph("<font color=#808080><b>Discalimer: Can't be used as an Official Document!</b></font>", styles['FooterItalic']))

        # Ensure everything fits on one page
        content = KeepTogether(story)

        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Marksheet_{student.student_id}_{semester.name}.pdf"'
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)



# Transcript Section
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


from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import landscape, A4, legal
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

# def transcript_landscape_view(request, student_id):
#     # Response setup
#     buffer = BytesIO()
#     p = canvas.Canvas(buffer, pagesize=landscape(legal))
#     width, height = landscape(legal)

#     # === HEADER PLACEHOLDER ===
#     p.setFont("Helvetica-Bold", 16)
#     p.drawCentredString(width / 2, height - 40, "UNIVERSITY NAME")
#     p.setFont("Helvetica", 12)
#     p.drawCentredString(width / 2, height - 60, "Transcript (Landscape Format)")

#     # Dummy data
#     data = [
#         ["S/L", "Student ID", "Name", "Hall", "EEE 511", "", "", "", "", "EEE 512", "", "", "", "",
#          "EEE 513", "", "", "", "", "EEE 514", "", "", "", "", "EEE 515", "", "", "", "",
#          "EEE 516", "", "", "", "", "CSE 517", "", "", "", "", "CSE 518", "", "", "", "",
#          "EEE 519", "", "", "", "", "TCP", "GPA", "Results", "Remarks"],
#         ["", "", "", "", "CATM", "FEM", "MO", "LG", "CP", "CATM", "FEM", "MO", "LG", "CP",
#          "CATM", "FEM", "MO", "LG", "CP", "CATM", "FEM", "MO", "LG", "CP",
#          "CATM", "FEM", "MO", "LG", "CP", "CATM", "FEM", "MO", "LG", "CP",
#          "CATM", "FEM", "MO", "LG", "CP", "CATM", "FEM", "MO", "LG", "CP",
#          "CATM", "FEM", "MO", "LG", "CP", "", "", "", ""],
#         [1, "21702002", "Abdul Mannan", "Shaheed Abdur Rab Hall",
#          18, 44, 92.75, "B+", 3.75, 10, 15, 30, "B", 3.00,
#          15, 58, 97.5, "A", 4.00, 18, 35, 83.5, "A-", 3.50,
#          53, 105, 90, "A", 4.00, 26, 56, 92, "B", 3.00,
#          10, 18, 30, "A+", 4.00, 38, 58, 96, "A", 4.00,
#          112.5, 4.00, "PASS", ""],
#         [2, "21702005", "Mokhlasur Rahaman", "Shaheed Abdur Rab Hall",
#          15, 40, 75, "C+", 2.50, 7.5, 15, 30, "B", 3.00,
#          13, 45, 80, "A-", 3.50, 17, 30, 70, "B+", 3.25,
#          28, 0, 0, "F", 0.00, 16, 56, 90, "A", 4.00,
#          18, 38, 92, "A", 4.00, 48, 53, 101, "A+", 4.00,
#          98.0, 3.75, "PASS", ""],
#     ]

#     # Table styling
#     table = Table(data, repeatRows=2)
#     style = TableStyle([
#         ('GRID', (0,0), (-1,-1), 0.5, colors.black),
#         ('ALIGN', (0,0), (-1,-1), 'CENTER'),
#         ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
#         ('SPAN', (0,0), (0,1)),  # S/L merge
#         ('SPAN', (1,0), (1,1)),  # Student ID
#         ('SPAN', (2,0), (2,1)),  # Name
#         ('SPAN', (3,0), (3,1)),  # Hall
#         ('SPAN', (4,0), (8,0)),  # EEE 511
#         ('SPAN', (9,0), (13,0)),  # EEE 512
#         ('SPAN', (14,0), (18,0)), # EEE 513
#         ('SPAN', (19,0), (23,0)), # EEE 514
#         ('SPAN', (24,0), (28,0)), # EEE 515
#         ('SPAN', (29,0), (33,0)), # EEE 516
#         ('SPAN', (34,0), (38,0)), # CSE 517
#         ('SPAN', (39,0), (43,0)), # CSE 518
#         ('SPAN', (44,0), (48,0)), # EEE 519
#         ('SPAN', (49,0), (49,1)), # TCP
#         ('SPAN', (50,0), (50,1)), # GPA
#         ('SPAN', (51,0), (51,1)), # Results
#         ('SPAN', (52,0), (52,1)), # Remarks
#     ])
#     table.setStyle(style)

#     # Draw table
#     table.wrapOn(p, width, height)
#     table.drawOn(p, 20, height - 200)

#     # === FOOTER PLACEHOLDER ===
#     p.setFont("Helvetica", 10)
#     p.drawString(40, 40, "Generated by University System")

#     p.showPage()
#     p.save()
#     buffer.seek(0)

#     return HttpResponse(buffer, content_type='application/pdf')



# Make sure to install reportlab: pip install reportlab





from reportlab.platypus import Table, TableStyle, Paragraph, Flowable
from reportlab.lib.styles import getSampleStyleSheet

# ✨ NEW: Class for drawing rotated text in table headers
# class VerticalText(Flowable):
#     """A flowable that draws text rotated 90 degrees."""
#     def __init__(self, text, font_name='Helvetica-Bold', font_size=7):
#         Flowable.__init__(self)
#         self.text = text
#         self.font_name = font_name
#         self.font_size = font_size

#     def draw(self):
#         canvas = self.canv
#         canvas.saveState()
#         canvas.setFont(self.font_name, self.font_size)
#         canvas.rotate(90)
#         # The coordinates are x, y. We draw slightly up from the bottom-left.
#         canvas.drawString(3, -self.width + 4, self.text)
#         canvas.restoreState()

#     def wrap(self, availableWidth, availableHeight):
#         # This is tricky. We are rotating, so the concepts of width/height are swapped.
#         self.width = availableHeight
#         # The height it needs is the width of the string.
#         self.height = self.canv.stringWidth(self.text, self.font_name, self.font_size)
#         return (self.width, self.height)

# def transcript_landscape_view(request, student_id):
#     buffer = BytesIO()
#     p = canvas.Canvas(buffer, pagesize=landscape(legal))
#     width, height = landscape(legal)

#     # --- ✨ NEW: Prepare styles for Paragraphs ---
#     styles = getSampleStyleSheet()
#     # Center-aligned style for Name/Hall cells
#     p_style = styles['Normal']
#     p_style.alignment = 1 # 0=left, 1=center, 2=right
#     p_style.leading = 10 # Line spacing

#     # --- Data for the Table ---
#     # Create the rotated sub-headers
#     sub_header_texts = ["CATM", "FEM", "MO", "CP", "LG"]
#     rotated_headers = [VerticalText(text) for text in sub_header_texts]

#     # Main student data list
#     students_data = [
#         [1, "21702002", "Abdul Mannan", "Shaheed Abdur Rab Hall", [18,44,62,3.00,"B"], [15,35,50,3.00,"B"], [15,40,55,3.25,"B+"] ],
#         [2, "21702005", "Mokhlasur Rahaman", "Shaheed Abdur Rab Hall", [10,40,50,3.00,"B"], [15,38,53,3.00,"B"], [17,33,50,3.00,"B"] ],
#         # ... add more student data in the same format
#     ]

#     # --- Build the table row-by-row ---
#     data = []
#     # Row 0: Main Headers
#     header_row_1 = ["S/L", "Student ID", "Name\nHall", "EEE 511", "", "", "", "", "EEE 512", "", "", "", "", "EEE 513", "", "", "", "", "Results", "Remarks"]
#     data.append(header_row_1)

#     # Row 1: Sub-headers (using rotated text)
#     header_row_2 = ["", "", ""]
#     for _ in range(3): # For 3 courses in this example
#         header_row_2.extend(rotated_headers)
#     header_row_2.extend(["", ""]) # For Results, Remarks
#     data.append(header_row_2)

#     # Add student rows
#     for student in students_data:
#         row = [
#             student[0],
#             student[1],
#             Paragraph(f"{student[2]}<br/>{student[3]}", p_style)
#         ]
#         # Add course data
#         for course in student[4:]:
#             row.extend(course)
#         row.extend(["PASS", ""]) # Add results and remarks
#         data.append(row)

#     # --- Define Column Widths ---
#     col_widths = [0.3*inch, 0.7*inch, 1.8*inch] # S/L, ID, Name/Hall
#     course_col_width = [0.4*inch] * 5
#     for _ in range(3): # For 3 courses
#         col_widths.extend(course_col_width)
#     col_widths.extend([0.7*inch, 1.2*inch]) # Results, Remarks

#     # --- Create Table and Apply Styles ---
#     table = Table(data, colWidths=col_widths, rowHeights=None, repeatRows=2)
#     style = TableStyle([
#         ('GRID', (0,0), (-1,-1), 0.5, colors.black),
#         ('ALIGN', (0,0), (-1,-1), 'CENTER'),
#         ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
#         ('FONTSIZE', (0,0), (-1,-1), 7),
#         ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), # Bold for top header

#         # Header background
#         ('BACKGROUND', (0,0), (-1,1), colors.lightgrey),
#         # Make name/hall cell text smaller
#         ('FONTSIZE', (2,2), (2,-1), 8),

#         # SPAN commands for cell merging
#         ('SPAN', (0,0), (0,1)),      # S/L
#         ('SPAN', (1,0), (1,1)),      # Student ID
#         ('SPAN', (2,0), (2,1)),      # Name/Hall
#         ('SPAN', (3,0), (7,0)),      # EEE 511
#         ('SPAN', (8,0), (12,0)),     # EEE 512
#         ('SPAN', (13,0), (17,0)),    # EEE 513
#         ('SPAN', (18,0), (18,1)),    # Results
#         ('SPAN', (19,0), (19,1)),    # Remarks
#     ])
#     table.setStyle(style)

#     # --- Draw the table ---
#     # The table is drawn from the bottom-left corner.
#     table.wrapOn(p, width, height)
#     table.drawOn(p, 20, 250) # x, y coordinates from bottom-left

#     # To repeat the table with a new set of students (as shown in your image)
#     # You would simply create and draw a second Table object below the first one.
#     # table2.drawOn(p, 20, 50)

#     p.showPage()
#     p.save()
#     buffer.seek(0)

#     return HttpResponse(buffer, content_type='application/pdf')



# ==============================================================================
# Full Code for Tabulation Sheet PDF Generation in Django
# ==============================================================================

# --- Python & Django Imports ---
import os
from io import BytesIO
from datetime import datetime
from decimal import Decimal, ROUND_CEILING

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum

# --- ReportLab Imports ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, legal
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, Flowable
from reportlab.lib.styles import getSampleStyleSheet

# --- ‼️ UPDATE THESE: Your Project's Models ---
# Make sure to import all the models you use for students, courses, and marks.
from .models import StudentProfile, Semester, Course, CTMark, AttendanceMark, FinalExamMark, LabMark
# from .models import ThesisMark, FieldWorkMark # etc.


# ==============================================================================
# Helper Classes & Functions
# ==============================================================================

class VerticalText(Flowable):
    """A flowable that draws text rotated 90 degrees for table headers."""
    def __init__(self, text, font_name='Helvetica-Bold', font_size=7):
        Flowable.__init__(self)
        self.text = text
        self.font_name = font_name
        self.font_size = font_size

    def draw(self):
        canv = self.canv
        canv.saveState()
        canv.setFont(self.font_name, self.font_size)
        canv.rotate(90)
        canv.drawString(3, -self.width + 4, self.text)
        canv.restoreState()

    def wrap(self, availableWidth, availableHeight):
        self.width = availableHeight
        self.height = self.canv.stringWidth(self.text, self.font_name, self.font_size)
        return (self.width, self.height)

def calculate_grade(percentage):
    """
    Calculates letter grade and grade point from a percentage.
    ‼️ UPDATE THIS with your university's grading policy.
    """
    percentage = Decimal(percentage)
    if percentage >= 80: return 'A+', 4.00
    if percentage >= 75: return 'A', 3.75
    if percentage >= 70: return 'A-', 3.50
    if percentage >= 65: return 'B+', 3.25
    if percentage >= 60: return 'B', 3.00
    if percentage >= 55: return 'B-', 2.75
    if percentage >= 50: return 'C+', 2.50
    if percentage >= 45: return 'C', 2.25
    if percentage >= 40: return 'D', 2.00
    return 'F', 0.00

def calculate_course_results(student, course):
    """
    Calculates marks, grade, and point for a student in a course.
    """
    try:
        course_type = course.course_type.lower()
        credit = course.credit
        total_mark = Decimal(0)
        ca_mark = Decimal(0)  # Continuous Assessment
        th_mark = Decimal(0)  # Theory/Final Exam

        if course_type == 'theory':
            ct_total = CTMark.objects.filter(student=student, course=course).aggregate(
                total=Sum('mark')
            )['total'] or 0
            # Assuming average of 3 class tests. Adjust if different.
            ct_avg = (Decimal(ct_total) / 3).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

            attendance_obj = AttendanceMark.objects.filter(student=student, course=course).first()
            attendance_mark = Decimal(attendance_obj.mark) if attendance_obj else Decimal(0)
            
            ca_mark = ct_avg + attendance_mark

            final_exam_obj = FinalExamMark.objects.filter(student=student, course=course).first()
            th_mark = Decimal(final_exam_obj.marks_obtained) if final_exam_obj else Decimal(0)

            total_mark = (ca_mark + th_mark).quantize(Decimal('0.01'))

        elif course_type == 'lab':
            lab_mark_obj = LabMark.objects.filter(student=student, course=course).first()
            if lab_mark_obj:
                # For labs, you might assign components differently or just show total
                ca_mark = Decimal(lab_mark_obj.quiz_viva) + Decimal(lab_mark_obj.attendance)
                th_mark = Decimal(lab_mark_obj.experiment) # As an example
                total_mark = (ca_mark + th_mark).quantize(Decimal('0.01'))
        
        # ‼️ Add your logic for 'thesis', 'field work', etc. here
        
        # If no marks found, return 'Not Applicable'
        if not total_mark and not ca_mark and not th_mark:
             return {'ca': '-', 'th': '-', 'total': '-', 'grade': '-', 'point': Decimal(0.0), 'credit': Decimal(credit)}

        # ‼️ UPDATE THIS: Max marks might not always be credit * 25
        max_marks = credit * 25 
        percentage = (total_mark / max_marks) * 100 if max_marks > 0 else 0
        grade, point = calculate_grade(percentage)

        return {
            'ca': ca_mark,
            'th': th_mark,
            'total': total_mark,
            'grade': grade,
            'point': Decimal(point),
            'credit': Decimal(credit),
        }

    except Exception as e:
        print(f"Error calculating marks for {student.student_id} in {course.course_code}: {e}")
        return {'ca': 'Err', 'th': 'Err', 'total': 'Err', 'grade': 'F', 'point': Decimal(0.0), 'credit': Decimal(credit)}


# ==============================================================================
# Main Django View
# ==============================================================================
ledger = (17 * inch, 10 * inch)
def generate_tabulation_sheet_view(request, student_id):
    """
    Generates a multi-student, landscape tabulation sheet PDF.
    """
    # --- 1. Fetch Data ---
    # ‼️ UPDATE THIS QUERY: Select the students you want on the sheet.
    students_to_include = StudentProfile.objects.all()
    
    # ‼️ UPDATE THIS QUERY: Get the ordered list of courses for the columns.
    # courses_to_include = Course.objects.all().order_by('semester__name', 'course_code')
    courses_to_include = Course.objects.filter(semester__name='1-1').order_by('course_code')

    # --- 2. Initialize PDF ---
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(legal))
    width, height = landscape(legal)
    
    left_margin = 0.3 * inch
    right_margin = width - 0.5 * inch
    center = width / 2

    # --- 3. Draw Static Header ---
    y_pos = height - 40
    try:
        if os.path.exists('static/img/university_logo.png'):
            p.drawImage('static/img/university_logo.png', left_margin, y_pos - 25, width=50, height=50, mask='auto')
        if os.path.exists('static/img/department_logo.png'):
            p.drawImage('static/img/department_logo.png', right_margin - 50, y_pos - 25, width=50, height=50, mask='auto')
    except Exception as e:
        print(f"Error loading logos: {e}")

    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(center, y_pos, "University of Chittagong")
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(center, y_pos - 20, "Faculty of Engineering")
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(center, y_pos - 38, "Department of Electrical & Electronic Engineering")
    p.setFont("Helvetica-Bold", 12)
    p.drawCentredString(center, y_pos - 55, "B.Sc. Engineering Examination")

    # --- 4. Prepare Table Data ---
    styles = getSampleStyleSheet()
    p_style = styles['Normal']
    p_style.alignment = 1  # Center alignment
    p_style.fontSize = 7
    p_style.leading = 9    # Line spacing

    # Define table headers
    header1 = ["S/L", "Student ID", "Name\nHall"]
    for course in courses_to_include:
        header1.extend([f"{course.course_code}\n({course.credit})", "", "", "", ""]) # Add credit to header
    header1.extend(["TCP", "TGP", "GPA", "Result", "Remarks"])

    header2 = ["", "", ""]
    rotated_subheaders = [VerticalText("CA"), VerticalText("TH"), VerticalText("Total"), VerticalText("LG"), VerticalText("GP")]
    for _ in courses_to_include:
        header2.extend(rotated_subheaders)
    header2.extend(["", "", "", "", ""])

    table_data = [header1, header2]

    # Populate table with student data
    for i, student in enumerate(students_to_include):
        student_row = [
            i + 1,
            student.student_id,
            Paragraph(f"<b>Namirah Tarannum</b><br/>{getattr(student, 'hall', 'N/A')}", p_style)
        ]
        
        total_credits_passed = Decimal(0)
        total_grade_points = Decimal(0)

        data_font = 'Helvetica'
        data_font_size = 6.5

        # for course in courses_to_include:
        #     results = calculate_course_results(student, course)
        #     student_row.extend([results['ca'], results['th'], results['total'], results['grade'], results['point']])
            
        #     if results['grade'] not in ['F', '-', 'N/A']:
        #         total_credits_passed += results['credit']
        #         total_grade_points += results['point'] * results['credit']
        for course in courses_to_include:
            results = calculate_course_results(student, course)
            
            student_row.extend([
                VerticalText(str(results['ca']), font_name=data_font, font_size=data_font_size),
                VerticalText(str(results['th']), font_name=data_font, font_size=data_font_size),
                VerticalText(str(results['total']), font_name=data_font, font_size=data_font_size),
                VerticalText(str(results['grade']), font_name=data_font, font_size=data_font_size),
                VerticalText(str(results['point']), font_name=data_font, font_size=data_font_size)
            ])
            
            if results['grade'] not in ['F', '-', 'N/A']:
                total_credits_passed += results['credit']
                total_grade_points += results['point'] * results['credit']
        
        gpa = (total_grade_points / total_credits_passed).quantize(Decimal('0.01')) if total_credits_passed > 0 else Decimal('0.00')
        result_status = "PASS" if gpa >= 2.00 else "FAIL" # Example logic

        # student_row.extend([total_credits_passed, total_grade_points, gpa, result_status, ""])
        student_row.extend([
            VerticalText(str(total_credits_passed), font_name=data_font, font_size=data_font_size),
            VerticalText(str(total_grade_points), font_name=data_font, font_size=data_font_size),
            VerticalText(str(gpa), font_name=data_font, font_size=data_font_size),
            result_status, # Result text remains horizontal for readability
            "" # Remarks remain horizontal
        ])
        table_data.append(student_row)

    # --- 5. Define Table Layout and Style ---
    col_widths = [0.3*inch, 0.6*inch, 1.4*inch]
    course_sub_widths = [0.28*inch, 0.28*inch, 0.28*inch, 0.28*inch, 0.28*inch]
    for _ in courses_to_include:
        col_widths.extend(course_sub_widths)

    # for _ in courses_to_include:
    #     col_widths.extend([0.35*inch] * 5)
    col_widths.extend([0.35*inch, 0.35*inch, 0.35*inch, 0.5*inch, 0.8*inch])
    

    main_table = Table(table_data, colWidths=col_widths, rowHeights=None, repeatRows=2)
    
    style = TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 6),
        ('FONTNAME', (0,0), (-1,1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (-1,1), colors.lightgrey),
        ('SPAN', (0,0), (0,1)), ('SPAN', (1,0), (1,1)), ('SPAN', (2,0), (2,1)),
        ('SPAN', (-5,0), (-5,1)), ('SPAN', (-4,0), (-4,1)), ('SPAN', (-3,0), (-3,1)),
        ('SPAN', (-2,0), (-2,1)), ('SPAN', (-1,0), (-1,1)),
    ])
    
    for i in range(len(courses_to_include)):
        start_col = 3 + (i * 5)
        end_col = start_col + 4
        style.add('SPAN', (start_col, 0), (end_col, 0))

    main_table.setStyle(style)

    # --- 6. Draw Table and Footer ---
    table_y_pos = height - 130 # Position table below header
    main_table.wrapOn(p, width, height)
    main_table.drawOn(p, left_margin, table_y_pos - main_table._height)
    
    footer_y = 0.3 * inch
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(center, footer_y + 10, "Generated by Ignite Result Management System")
    p.drawCentredString(center, footer_y, f"Date of Publication: {datetime.now().strftime('%B %d, %Y')}")

    # --- 7. Finalize and Return PDF ---
    p.showPage()
    p.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="tabulation_sheet.pdf"'
    return response



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



# Student Ct marks
def student_ct_marks(request):
    student = request.user.studentprofile  # Assuming you have a StudentProfile linked with User
    
    students = StudentProfile.objects.filter(id=student.id)
    semesters = Semester.objects.all()

    selected_semester_id = request.GET.get('semester')
    ct_marks = None

    if selected_semester_id:
        ct_marks = CTMark.objects.filter(
            student=student,
            semester_id=selected_semester_id
        ).select_related('course', 'semester')

    return render(request, 'marks/student_ct_marks.html', {
        'semesters': semesters,
        'selected_semester_id': selected_semester_id,
        'ct_marks': ct_marks,
        'students': students,
    })


# Student Attendance marks
def student_attendance_marks(request):
    student = request.user.studentprofile  # assuming relation User -> StudentProfile
    print('attendance student', student)
    semesters = Semester.objects.all()

    students = StudentProfile.objects.filter(id=student.id)
    print('attandance students', students)

    selected_semester_id = request.GET.get('semester')
    attendance_marks = []

    if selected_semester_id:
        attendance_marks = AttendanceMark.objects.filter(
            student=student,
            semester_id=selected_semester_id
        ).select_related('course', 'semester')

    return render(request, 'marks/student_attendance_marks.html', {
        'semesters': semesters,
        'attendance_marks': attendance_marks,
        'selected_semester_id': int(selected_semester_id) if selected_semester_id else None,
        'students': students,
    })


# Student Final Exam marks
def student_final_marks(request):
    student = request.user.studentprofile
    print('final student', student)

    students = StudentProfile.objects.filter(id=student.id)
    print('final students', students)

    semesters = Semester.objects.all()
    selected_semester_id = request.GET.get("semester")
    final_marks = None

    if selected_semester_id:
        final_marks = FinalExamMark.objects.filter(
            student=student, 
            semester_id=selected_semester_id
        ).select_related("course", "semester")
    
    print('final_marks', final_marks)

    return render(request, "marks/student_final_marks.html", {
        "semesters": semesters,
        "final_marks": final_marks,
        "selected_semester_id": selected_semester_id,
        "students": students,
    })


def student_result_overview(request):
    semesters = Semester.objects.all()
    return render(request, 'marks/student_result_overview.html', {
        'semesters': semesters
    })


def get_result_overview(request):
    student = request.user.studentprofile  # assuming OneToOne relation
    semester_id = request.GET.get('semester_id')

    if not semester_id:
        return JsonResponse({"error": "Semester ID is required"}, status=400)

    courses = Course.objects.filter(semester_id=semester_id, course_type="theory")
    results = []

    for course in courses:
        ct_mark = CTMark.objects.filter(student=student, course=course).first()
        ct_avg = (Decimal(ct_mark)/3).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if ct_mark else Decimal(0)
        attendance_mark = AttendanceMark.objects.filter(student=student, course=course).first()
        final_mark = FinalExamMark.objects.filter(student=student, course=course).first()

        total_mark = Decimal('0.0')
        total_mark += Decimal(ct_mark.mark) if ct_mark and ct_mark.mark is not None else Decimal('0.0')
        total_mark += Decimal(attendance_mark.mark) if attendance_mark and attendance_mark.mark is not None else Decimal('0.0')
        total_mark += Decimal(final_mark.marks_obtained) if final_mark and final_mark.marks_obtained is not None else Decimal('0.0')

        results.append({
            "course_code": course.course_code,
            "course_name": course.course_name,
            "ct_mark": float(ct_mark.mark) if ct_mark and ct_mark.mark is not None else None,
            "attendance_mark": float(attendance_mark.mark) if attendance_mark and attendance_mark.mark is not None else None,
            "final_mark": float(final_mark.marks_obtained) if final_mark and final_mark.marks_obtained is not None else None,
            "total_mark": float(total_mark)
        })

    return JsonResponse(results, safe=False)


def student_marksheet_panel(request):
    student = request.user.studentprofile  # Only the logged-in student
    semesters = Semester.objects.all()

    selected_semester_id = request.GET.get('semester')
    result_data = []
    gpa = Decimal('0.00')

    if selected_semester_id:
        semester = Semester.objects.get(id=selected_semester_id)
        courses = Course.objects.filter(semester=semester)

        total_credits = 0
        total_grade_points = Decimal('0.00')

        for course in courses:
            try:
                course_type = course.course_type.lower()
                credit = course.credit
                total_mark = Decimal('0.00')

                # THEORY
                if course_type == 'theory':
                    ct_marks = CTMark.objects.filter(student=student, course=course).aggregate(total=Sum('mark'))['total'] or Decimal('0.0')
                    ct_avg = (ct_marks / 3).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if ct_marks else Decimal('0.0')

                    attendance = AttendanceMark.objects.filter(student=student, course=course).first()
                    attendance_mark = Decimal(attendance.mark).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if attendance else Decimal('0.0')

                    final_exam = FinalExamMark.objects.filter(student=student, course=course).first()
                    final_mark = Decimal(final_exam.marks_obtained).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if final_exam else Decimal('0.0')

                    total_mark = (ct_avg + attendance_mark + final_mark).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

                # LAB
                elif course_type == 'lab' and LabMark.objects.filter(student=student, course=course).exists():
                    lab_mark = LabMark.objects.get(student=student, course=course)
                    total_mark = (
                        Decimal(lab_mark.quiz_viva) +
                        Decimal(lab_mark.experiment) +
                        Decimal(lab_mark.attendance)
                    ).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

                # THESIS
                elif course_type == 'thesis' and ThesisMark.objects.filter(student=student, course=course).exists():
                    thesis_mark = ThesisMark.objects.get(student=student, course=course)
                    total_mark = (
                        Decimal(thesis_mark.internal) +
                        Decimal(thesis_mark.external) +
                        Decimal(thesis_mark.presentation)
                    ).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

                # FIELD WORK
                elif course_type == 'field work' and FieldWorkMark.objects.filter(student=student, course=course).exists():
                    field_mark = FieldWorkMark.objects.get(student=student, course=course)
                    total_mark = Decimal(field_mark.field_mark).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

                else:
                    continue  # Skip unknown course types or missing marks

                # Percentage and Grade
                max_total = credit * 25  # Assuming max marks per credit
                percentage = (total_mark / max_total) * 100
                grade, point = calculate_grade(float(percentage))

                result_data.append({
                    'course': course,
                    'credit': credit,
                    'total_mark': total_mark,
                    'percentage': round(percentage, 2),
                    'grade': grade,
                    'point': point,
                })

                total_credits += credit
                total_grade_points += Decimal(point) * Decimal(credit)

            except Exception as e:
                print(f"Error processing course {course.course_name}: {e}")
                continue

        gpa = (total_grade_points / Decimal(total_credits)).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if total_credits > 0 else Decimal('0.00')

        # PDF export
        if 'export_pdf' in request.GET:
            context = {
                'student': student,
                'semester': semester,
                'result_data': result_data,
                'gpa': gpa
            }
            html = render_to_string('marks/student_marksheet_pdf.html', context)
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=Marksheet_{student.student_id}_{semester.name}.pdf'
            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('Error generating PDF')
            return response

    context = {
        'student': student,
        'semesters': semesters,
        'selected_semester_id': selected_semester_id,
        'result_data': result_data,
        'gpa': gpa
    }
    return render(request, 'marks/student_marksheet_panel.html', context)

from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from io import BytesIO
import os
from decimal import Decimal, ROUND_CEILING
from django.db.models import Sum
from reportlab.platypus.flowables import Image
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

def student_marksheet_pdf(request, semester_id):
    student = request.user.studentprofile
    print('student', student)
    semester = Semester.objects.get(id=semester_id)
    courses = Course.objects.filter(semester=semester)

    student_info = StudentProfile.objects.get(id=student.id)
    print('studetn info', student_info)

    result_data = []
    total_credits = 0
    total_grade_points = Decimal('0.00')

    for course in courses:
        # Copy your calculation logic from generate_marksheet
        # For brevity, assuming you already have total_mark, grade, point
        course_type = course.course_type.lower()
        credit = course.credit
        total_mark = Decimal(0)

        if course_type == 'theory':
            ct_marks = CTMark.objects.filter(student=student, course=course).aggregate(
                total=Sum('mark')
            )['total'] or 0
            ct_avg = (Decimal(ct_marks) / 3).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if ct_marks else Decimal(0)
            attendance = AttendanceMark.objects.filter(student=student, course=course).first()
            attendance_mark = Decimal(attendance.mark).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if attendance else Decimal(0)
            final_exam = Decimal(FinalExamMark.objects.get(student=student, course=course).marks_obtained).quantize(Decimal('0.01'), rounding=ROUND_CEILING) if FinalExamMark.objects.filter(student=student, course=course).exists() else Decimal(0)

            total_mark = (
                (Decimal(ct_avg) +
                (Decimal(attendance_mark)  +
                (Decimal(final_exam) )))
            ).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

        elif course_type == 'lab':
            lab_mark = LabMark.objects.get(student=student, course=course)
            total_mark = (
                Decimal(lab_mark.quiz_viva).quantize(Decimal('0.01'), rounding=ROUND_CEILING) +
                Decimal(lab_mark.experiment).quantize(Decimal('0.01'), rounding=ROUND_CEILING) +
                Decimal(lab_mark.attendance).quantize(Decimal('0.01'), rounding=ROUND_CEILING)
            ).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

        elif course_type == 'thesis':
            thesis_mark = ThesisMark.objects.get(student=student, course=course)
            total_mark = (
                Decimal(thesis_mark.internal).quantize(Decimal('0.01'), rounding=ROUND_CEILING) +
                Decimal(thesis_mark.external).quantize(Decimal('0.01'), rounding=ROUND_CEILING) +
                Decimal(thesis_mark.presentation).quantize(Decimal('0.01'), rounding=ROUND_CEILING)
            ).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

        elif course_type == 'field work':
            field_work = FieldWorkMark.objects.get(student=student, course=course)
            total_mark = Decimal(field_work.field_mark).quantize(Decimal('0.01'), rounding=ROUND_CEILING)

        else:
            continue  # skip if unknown course_type

        # Normalize based on credit
        max_total = credit * 25
        percentage = (total_mark / max_total) * 100
        grade, point = calculate_grade(percentage)
        result_data.append({
            'course': course,
            'credit': course.credit,
            'grade': grade,
            'point': point
        })
        print('result data', result_data)
        total_credits += course.credit
        total_grade_points += Decimal(point) * Decimal(course.credit)

    gpa = (total_grade_points / Decimal(total_credits)).quantize(Decimal('0.01')) if total_credits > 0 else Decimal('0.00')
    result_status = "P" if all(item['point'] > 0 for item in result_data) else "F"


    # Create the PDF using ReportLab
    # PDF Generation
    buffer = BytesIO()
    # Use A4 size with appropriate margins to match the reference
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=10*mm,
        bottomMargin=15*mm
    )
    
    # Custom styles
    styles = getSampleStyleSheet()
    
    # University header style
    styles.add(ParagraphStyle(
        'UniversityHeader',
        parent=styles['Normal'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    ))
    
    # Department style
    styles.add(ParagraphStyle(
        'Department',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    ))
    
    # Exam info style
    styles.add(ParagraphStyle(
        'ExamInfo',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=6
    ))
    
    # Grade Sheet title
    styles.add(ParagraphStyle(
        'GradeSheetTitle',
        parent=styles['Normal'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceBefore=12,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    ))
    
    # Student info style
    styles.add(ParagraphStyle(
        'StudentInfo',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=3
    ))
    
    # Table header style
    styles.add(ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    # Table content style
    styles.add(ParagraphStyle(
        'TableContent',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER
    ))
    
    # Formula style
    styles.add(ParagraphStyle(
        'Formula',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT,
        spaceAfter=3
    ))
    
    # Summary style
    styles.add(ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=3
    ))
    
    # Footer style
    styles.add(ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=3
    ))
    
    story = []
    
    # Header - University information
    logo_path = os.path.join('static', 'img', 'university_logo.png')
    if os.path.exists(logo_path):
        try:
            logo = RLImage(logo_path, width=1.5*inch, height=1.5*inch)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 12))
        except:
            story.append(Paragraph("University of Chittagong", styles['CenterTitle']))
    else:
        story.append(Paragraph("University of Chittagong", styles['CenterTitle']))
    
    story.append(Paragraph("UNIVERSITY OF CHITTAGONG", styles['UniversityHeader']))
    story.append(Paragraph("CHITTAGONG, BANGLADESH", styles['ExamInfo']))
    story.append(Paragraph("Department of Electrical and Electronic Engineering", styles['Department']))
    story.append(Paragraph("Seventh Semester B. Sc. Engineering Examination-2020", styles['ExamInfo']))
    story.append(Paragraph("Held in February - November, 2021", styles['ExamInfo']))
    story.append(Spacer(1, 12))
    
    # Grade Sheet title
    story.append(Paragraph("Grade Sheet", styles['GradeSheetTitle']))
    
    # Student information
    student_info_data = [
        [Paragraph("<b>Student ID</b>", styles['StudentInfo']), Paragraph(f": {student.student_id}", styles['StudentInfo'])],
        [Paragraph("<b>Name of the Student</b>", styles['StudentInfo']), Paragraph(f": {student.full_name}", styles['StudentInfo'])],
        [Paragraph("<b>Name of the Hall</b>", styles['StudentInfo']), Paragraph(f": {student.hall}", styles['StudentInfo'])],
        [Paragraph("<b>Session</b>", styles['StudentInfo']), Paragraph(f": {student.session}", styles['StudentInfo'])]
    ]
    
    student_table = Table(student_info_data, colWidths=[1.5*inch, 4*inch])
    student_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        # ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
    ]))
    
    story.append(student_table)
    story.append(Spacer(1, 12))
    
    # Course results table
    table_data = [
        [
            Paragraph("Course Code", styles['TableHeader']),
            Paragraph("Course Title", styles['TableHeader']),
            Paragraph("Credits", styles['TableHeader']),
            Paragraph("Letter Grade", styles['TableHeader']),
            Paragraph("Grade Point", styles['TableHeader'])
        ]
    ]
    
    for item in result_data:
        table_data.append([
            Paragraph(item['course'].course_code, styles['TableContent']),
            Paragraph(item['course'].course_name, styles['TableContent']),
            Paragraph(str(item['credit']), styles['TableContent']),
            Paragraph(item['grade'], styles['TableContent']),
            Paragraph(f"{item['point']:.2f}", styles['TableContent'])
        ])
    
    # Create table with appropriate column widths
    course_table = Table(table_data, colWidths=[1.0*inch, 3.0*inch, 0.6*inch, 0.9*inch, 0.9*inch])
    course_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),  # Use string 'CENTER' not TA_CENTER
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('INNERGRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    
    story.append(course_table)
    story.append(Spacer(1, 12))

    # Summary information
    summary_data = [
        [Paragraph("<b>Total Credits Offered</b>", styles['Summary']), Paragraph(f": {total_credits}", styles['Summary'])],
        [Paragraph("<b>Total Credits Earned</b>", styles['Summary']), Paragraph(f": {total_credits}", styles['Summary'])],
        [Paragraph("<b>GPA</b>", styles['Summary']), Paragraph(f": {gpa:.2f}", styles['Summary'])],
        [Paragraph("<b>Result</b>", styles['Summary']), Paragraph(f": {result_status}", styles['Summary'])]
    ]
    
    summary_table = Table(summary_data, colWidths=[1.5*inch, 1.0*inch])
    summary_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 12))
    
    # Footer with dates and signatures
    story.append(Paragraph(f"Date of Publication: 09 JAN 2022", styles['Footer']))
    story.append(Spacer(1, 24))
    
    # Signature area (exactly as in the reference image)
    signature_data = [
        [
            Paragraph("Prepared By:..............................", styles['Footer']),
            Paragraph("Date of Issue:..............................", styles['Footer']),
            Paragraph("Compared By:..............................", styles['Footer'])
        ],
        [
            "",
            "",
            Paragraph("Controller of Examinations", styles['Footer'])
        ],
        [
            "",
            "",
            Paragraph("University of Chittagong", styles['Footer'])
        ]
    ]
    
    signature_table = Table(signature_data, colWidths=[2.0*inch, 2.0*inch, 2.0*inch])
    signature_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),  # Use string 'LEFT' not TA_LEFT
        ('ALIGN', (1,0), (1,-1), 'CENTER'),  # Use string 'CENTER' not TA_CENTER
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),  # Use string 'RIGHT' not TA_RIGHT
    ]))
    
    story.append(signature_table)
    
    # Build PDF
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create HTTP response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Marksheet_{student.student_id}_{semester.name}.pdf"'
    response.write(pdf)
    
    return response


def student_marksheet_pdf_demo(request):
    return render(request, 'marks/student_marksheet_pdf_demo.html')