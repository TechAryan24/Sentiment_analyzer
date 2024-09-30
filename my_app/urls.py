from django.contrib import admin
from django.urls import path
from my_app import views

urlpatterns = [
    path("",views.index, name="home"),
    path("login/",views.login, name="login"),
    path("signup/",views.signup, name="signup"),
     path("result/",views.result, name="result") 
]
