from django.shortcuts import render
from django.http import HttpResponse
from .sentiment_analyzer import analyze_comments, generate_description  # Import your analysis functions

# Create your views here.
def index(request):
    return render (request,'index.html')

def login(request):
    return render (request,'login.html')

def result(request):
    return render (request,'result.html')

def signup(request):
    return render (request,'signup.html')

