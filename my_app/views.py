from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import HttpResponse
from . import sentiment_analysis as sa
from .models import User
from .models import VideoSentiment
from django.contrib import messages
import math

# Create your views here.
def index(request):
    return render (request,'index.html')

# def login(request):
#     return render (request,'login.html')

def signup(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check if the email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('signup')

        # Save user data to the database
        user = User.objects.create(name=name, email=email, password=password)
        user.save()

        messages.success(request, 'User created successfully.')
        return redirect('login')

    return render(request, 'signup.html')


# Login view
def login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Verify user credentials
        try:
            user = User.objects.get(email=email, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            # Store the user's name in session to display in index.html
            request.session['user_name'] = user.name
            messages.success(request, "You have logged in successfully!")
            return redirect('home')  # Redirect to homepage
        else:
            messages.error(request, "Invalid email or password!")

    return render(request, 'login.html')

    # Logout view (optional)
def logout(request):
    auth_logout(request)
    # Clear the session to ensure user data is removed
    request.session.flush()  # This will clear all session data
    return redirect('home')  # Redirect to home page

def result(request):
    if request.method == 'POST':
        youtube_url = request.POST.get('youtube_url')
        description = request.POST.get('description')
        
        # Get selected categories from the form
        selected_categories = request.POST.get('categories', '').split(',')

        # Trigger the YouTube comment analysis
        comments, video_id = sa.analyze_comments(youtube_url)

        # Check if the video has already been analyzed
        video_sentiment = VideoSentiment.objects.filter(video_id=video_id).first()
        
        if video_sentiment:
            # Video has been analyzed, use stored values
            positive_count = video_sentiment.positive_count
            negative_count = video_sentiment.negative_count
            neutral_count = video_sentiment.neutral_count
            generated_description = video_sentiment.gen_description
            result = video_sentiment.result

            total = positive_count + negative_count + neutral_count

            #Percentage count for the chart
            if total > 0:
                pos_percentage = int((positive_count / total) * 100)
                neg_percentage = int((negative_count / total) * 100)
                neu_percentage = int((neutral_count / total) * 100)
            else:
                pos_percentage = neg_percentage = neu_percentage = 0

            # Deserialize comments
            positive_comments_var = video_sentiment.get_positive_comments()
            negative_comments_var = video_sentiment.get_negative_comments()

            # Get video details
            video_details = sa.get_video_details(youtube_url)

            # Pass the results to the template
            context = {
                'description': generated_description,
                'result': result,
                'pos_percentage': pos_percentage,
                'neg_percentage': neg_percentage,
                'neu_percentage': neu_percentage,
            }
        else: 
            #Extract keywords from description
            partialKeywords = sa.gen_keyword(description)
            
            keywords = []

            # Combine selected categories and keywords from description
            keywords = selected_categories + partialKeywords
            
            print(f"Length of keywords: {len(keywords)}") 
            print(f"keywords: {keywords}")
            #Filter comments
            rel_comments = sa.filtering(comments,keywords)
            
            #Analyze sentiment
            positive_count, negative_count, neutral_count, positive_comments_var,negative_comments_var,neutral_comments_var = sa.analyse_sentiment(rel_comments)

            total = positive_count + negative_count + neutral_count
            print(f"total: {total}")
            # Generate the description
            generated_description, result = sa.gen_desc(positive_count, negative_count, neutral_count, positive_comments_var,negative_comments_var,neutral_comments_var)
            
            # Save the analysis result to the database
            video_sentiment = VideoSentiment.objects.create(
                video_id=video_id,
                positive_count=positive_count,
                negative_count=negative_count,
                neutral_count=neutral_count,
                gen_description=generated_description,
                result=result,
            )

            # Serialize and save the lists
            video_sentiment.set_positive_comments(positive_comments_var)
            video_sentiment.set_negative_comments(negative_comments_var)

            video_sentiment.save()

        # Get video details
        video_details = sa.get_video_details(youtube_url)

        print(f"Positive count in views: {positive_count}")
        #Percentage count for the chart
        pos_percentage = int((positive_count/total) * 100)
        neg_percentage = int((negative_count/total) * 100)
        neu_percentage = int((neutral_count/total) * 100)

        # Pass the results to the template
        context = {
            'description': generated_description,
            'result': result,
            'positive_comments': positive_comments_var,  
            'negative_comments': negative_comments_var, 
            'title': video_details['title'],
            'published_at': video_details['published_at'],
            'views': video_details['views'],
            'likes': video_details['likes'],
            'dislikes': video_details['dislikes'],
            'comments': video_details['comments'],
            'pos_percentage': pos_percentage,
            'neg_percentage': neg_percentage,
            'neu_percentage': neu_percentage,
        }
        
        return render(request, 'result.html', context)

    # In case of a GET request, just show an empty form or redirect
    return render(request, 'index.html')