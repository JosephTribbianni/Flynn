#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.urls import path
from accounting import views

urlpatterns = [
    path('login/', views.Login.as_view()),
    path('register/', views.Register.as_view()),
    path('logout/', views.Logout.as_view()),
    path('change/', views.PasswordChange.as_view())
]
