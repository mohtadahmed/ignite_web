from django.urls import path
from . import views


urlpatterns = [
    # add your URL paths here in the future
    path('add-ct-marks/', views.enter_ct_marks, name='add_ct_marks'),
    path('get-ct-marks/', views.get_ct_marks, name='get_ct_marks'),
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
    path('get-courses/', views.get_courses_by_semester, name='get_courses_by_semester'),
    path('get-students/', views.get_students_for_attendance, name='get_students_for_attendance'),
    path('save-attendance/', views.save_attendance_marks, name='save_attendance_marks'),

    path('marks_view/', views.marks_view, name='marks_view'),

    path('add-final-exam-marks/', views.add_final_exam_marks, name='add_final_exam_marks'),


    path('assign-final-marks/', views.assign_final_exam_marks, name='assign_final_exam_marks'),
    path('add-final-marks/<int:course_id>/', views.add_final_exam_marks, name='add_final_exam_marks'),

]
