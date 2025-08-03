from django.urls import path
from . import views


urlpatterns = [
    path('test/', views.generic_base, name='generic-base'),
    path('upload-routine/', views.upload_routine, name='upload_routine'),
    path('view-routines/', views.view_routines, name='view_routines'),
    path('upload-resource/', views.upload_resource, name='upload_resource'),
    path('resource-library/', views.resource_library, name='resource_library'),
    path('add-schedules/', views.add_schedule, name='add_schedule'),
    path('get-schedules/', views.student_schedule_list, name='student_schedule_list'),
]
