from django.urls import path
from . import views


urlpatterns = [
    path('test/', views.generic_base, name='generic-base'),
]
