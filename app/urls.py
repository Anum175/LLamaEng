# app/urls.py
from django.urls import path

from . import views

urlpatterns = [

    path('', views.text_labelling,name='text_labelling'),
    path('picture_labelling/', views.picture_labelling,name='picture_labelling'),
    path('data_preprocessing/', views.data_preprocessing,name='data_preprocessing'),

]