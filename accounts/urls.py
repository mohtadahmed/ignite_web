from django.urls import path
from . import views

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # HTML views
    path('dashboard/', views.dashboard, name='dashboard'),
    path('faculty_dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/edit/<int:student_id>/', views.edit_student, name='edit_student'),
    path('students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    path('students/bulk-upload/', views.student_bulk_upload, name='student_bulk_upload'),
    path('students/sample-csv/', views.download_sample_csv, name='download_sample_csv'),

    path('courses/add/', views.course_add, name='course_add'),
    path('courses/', views.course_list, name='course_list'),

    path('assign-courses/', views.assign_courses_to_student, name='assign_courses_to_student'),
    
    path('courses/assign/', views.assign_faculty_to_course, name='assign_faculty_to_course'),
    path('courses/assignments/', views.assigned_courses_list, name='assigned_courses_list'),

    path('faculty/create/', views.create_faculty, name='create_faculty'),
    path('faculty/', views.faculty_list, name='faculty_list'),


    # API views
    path('api/register/', views.register_user, name='api-register'),
    path('api/login/', views.login_user, name='api-login'),
    path('api/logout/', views.logout_user, name='api-logout'),
    path('api/reset-password/', views.reset_password, name='api-reset-password'),
    path('api/request-password-reset/', views.request_password_reset, name='api-request-password-reset'),
    path('api/reset-password/<uidb64>/<token>/', views.reset_password_confirm, name='api-password-reset-confirm'),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]