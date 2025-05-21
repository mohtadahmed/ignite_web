from django.urls import path
from . import views


urlpatterns = [
    # add your URL paths here in the future
    path('add-ct-marks/', views.add_ct_marks, name='add_ct_marks'),
    path('add-assignment-marks/', views.add_assignment_marks, name='add_assignment_marks'),
    path('add-quiz-marks/', views.add_quiz_marks, name='add_quiz_marks'),
    path('ct-marks/', views.ct_marks_list, name='ct_marks_list'),
    path('assignment-marks/', views.assignment_marks_list, name='assignment_marks_list'),
    path('quiz-marks/', views.quiz_marks_list, name='quiz_marks_list'),

    path('marks_view/', views.marks_view, name='marks_view'),

    path('add-final-exam-marks/', views.add_final_exam_marks, name='add_final_exam_marks'),


    path('assign-final-marks/', views.assign_final_exam_marks, name='assign_final_exam_marks'),
    path('add-final-marks/<int:course_id>/', views.add_final_exam_marks, name='add_final_exam_marks'),

]
