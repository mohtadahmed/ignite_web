from .models import *
from django.db.models import Sum

def calculate_grade(percentage):
    grading_scheme = [
        (80, 'A+', 4.0),
        (75, 'A', 3.75),
        (70, 'A-', 3.5),
        (65, 'B+', 3.25),
        (60, 'B', 3.0),
        (55, 'B-', 2.75),
        (50, 'C+', 2.5),
        (45, 'C', 2.25),
        (40, 'D', 2.0),
        (0, 'F', 0.0)
    ]

    # for threshold, grade, point in grading_scheme:
    #     if total_mark >= threshold:
    #         return {
    #             'grade': grade,
    #             'grade_point': point
    #         }
    for threshold, grade, point in grading_scheme:
        if percentage >= threshold:
            return grade, point
        

def calculate_final_results(course_id):
    course = Course.objects.get(id=course_id)
    credit = course.credit

    # Determine total marks based on credit
    total_marks_by_credit = {
        4: 100,
        3: 75,
        2: 50,
        1: 25
    }
    max_total_marks = total_marks_by_credit.get(credit, 100)  # fallback to 100

    results = []
    students = StudentProfile.objects.all()

    for student in students:
        ct_marks = CTMark.objects.filter(course=course, student=student).aggregate(total=Sum('mark'))['total'] or 0
        att_mark = AttendanceMark.objects.filter(course=course, student=student).first()
        att = att_mark.mark if att_mark else 0
        final = FinalExamMark.objects.filter(course=course, student=student).first()
        final_mark = final.mark if final else 0

        total = ct_marks + att + final_mark

        # Scale percentage
        percentage = (total / max_total_marks) * 100 if max_total_marks else 0

        grade, grade_point = calculate_grade(percentage)

        results.append({
            'student_id': student.student_id,
            'name': student.user.name,
            'total_marks': total,
            'percentage': round(percentage, 2),
            'grade': grade,
            'grade_point': grade_point,
        })

    return results
