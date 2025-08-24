from django.urls import path
from . import views


urlpatterns = [
    # add your URL paths here in the future
    path('add-ct-marks/', views.enter_ct_marks, name='add_ct_marks'),
    path('get-ct-marks/', views.get_ct_marks, name='get_ct_marks'),
    path("ct-marks/get-students/", views.get_students_by_semester, name="get_students_by_semester"),
    path("ct-marks/get-marks/", views.get_ct_marks_new, name="get_ct_marks_new"),
    path('save-ct-marks/', views.save_ct_marks, name='save_ct_marks'),

    # path('add-assignment-marks/', views.add_assignment_marks, name='add_assignment_marks'),
    path('add-assignment-marks/', views.add_assignment_marks, name='add_assignment_marks'),
    path('get_assignment_marks/', views.get_assignment_marks, name='get_assignment_marks'),
    path('get_latest_assignment_title/', views.get_latest_assignment_title, name='get_latest_assignment_title'),
    path('get_assignment_titles/', views.get_assignment_titles, name='get_assignment_titles'),
    path('save-assignment-marks/', views.save_assignment_marks, name='save_assignment_marks'),
    
    path('add-quiz-marks/', views.add_quiz_marks, name='add_quiz_marks'),
    path('ct-marks/', views.ct_marks_list, name='ct_marks_list'),
    path('assignment-marks/', views.assignment_marks_list, name='assignment_marks_list'),
    path('quiz-marks/', views.quiz_marks_list, name='quiz_marks_list'),

    path('attendance/', views.attendance_mark_entry, name='attendance_mark_entry'),
    path("attendance-marks/", views.attendance_marks_list, name="attendance_marks_list"),
    path("attendance-marks/get-students/", views.get_students_by_semester, name="attendance_students"),
    path("attendance-marks/get-marks/", views.get_attendance_marks, name="attendance_marks"),

    path('get-courses/', views.get_courses_by_semester, name='get_courses_by_semester'),
    path('get-students/', views.get_students_for_attendance, name='get_students_for_attendance'),
    path('save-attendance/', views.save_attendance_marks, name='save_attendance_marks'),

    path('marks_view/', views.marks_view, name='marks_view'),

    # path('add-final-exam-marks/', views.add_final_exam_marks, name='add_final_exam_marks'),


    path('assign-final-marks/', views.assign_final_exam_marks, name='assign_final_exam_marks'),
    # path('add-final-marks/<int:course_id>/', views.add_final_exam_marks, name='add_final_exam_marks'),

    path('add_final_exam_mark/', views.add_final_exam_mark, name='add_final_exam_mark'),
    path('final_result/', views.final_result_panel, name='final_result_panel'),
    path('set-mark-distribution/', views.set_mark_distribution, name='set_mark_distribution'),
    path('get_students_by_course/', views.get_students_by_course, name='get_students_by_course'),

    path('student-marksheet/', views.student_marksheet_view, name='student_marksheet'),
    path('marksheet/', views.generate_marksheet, name='generate_marksheet'),
    path('show-marksheet/', views.show_marksheet, name='show_marksheet'),

    path('lab-marks/', views.lab_mark_entry, name='lab_mark_entry'),

    path('add-thesis-mark/', views.add_thesis_mark, name='add_thesis_mark'),

    path('field-work-mark-entry/', views.field_work_mark_entry, name='field_work_mark_entry'),

    path('transcript_view/', views.transcript_view, name='transcript_view'),
    path('marksheet/pdf/<int:student_id>/<int:semester_id>/', views.generate_marksheet_pdf, name='generate_marksheet_pdf'),

    path('transcript-landscape/<int:student_id>/', views.generate_tabulation_sheet_view, name='transcript_landscape_view'),


    path('student_ct_marks', views.student_ct_marks, name='student_ct_marks'),
    path('student_attendance_marks', views.student_attendance_marks, name='student_attendance_marks'),
    path('student_final_marks', views.student_final_marks, name='student_final_marks'),
    path("get_result_overview/", views.get_result_overview, name="get_result_overview"),
    path("student_result_overview/", views.student_result_overview, name="student_result_overview"),

    path('student_marksheet_panel/', views.student_marksheet_panel, name='student_marksheet_panel'),
    
    path('marksheet/pdf/<int:semester_id>/', views.student_marksheet_pdf, name='student_marksheet_pdf'),
    path('student_marksheet_pdf_demo/', views.student_marksheet_pdf_demo, name='student_marksheet_pdf_demo'),

]
