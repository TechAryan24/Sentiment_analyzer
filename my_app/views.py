from django.shortcuts import render
from django.http import HttpResponse
from . import sentiment_analysis as sa
import math

# Create your views here.
def index(request):
    return render (request,'index.html')

def login(request):
    return render (request,'login.html')

def signup(request):
    return render (request,'signup.html')

def result(request):
    if request.method == 'POST':
        youtube_url = request.POST.get('youtube_url')
        description = request.POST.get('description')
        
        # Get selected categories from the form
        selected_categories = request.POST.get('categories', '').split(',')

        # Trigger the YouTube comment analysis
        comments = sa.analyze_comments(youtube_url)
        
        #Extract keywords from description
        partialKeywords = sa.gen_keyword(description)
        
        keywords = []

        # Combine selected categories and keywords from description
        keywords = selected_categories + partialKeywords
        
        print(f"Length of comments: {len(comments)}") 
        print(f"Length of keywords: {len(keywords)}") 
        print(f"keywords: {keywords}")
        #Filter comments
        rel_comments = sa.filtering(comments,keywords)
        total = len(rel_comments)
        
        #Analyze sentiment
        positive_count, negative_count, neutral_count, positive_comments_var,negative_comments_var,neutral_comments_var = sa.analyse_sentiment(rel_comments)

        # Generate the description
        generated_description, result = sa.gen_desc(positive_count, negative_count, neutral_count, positive_comments_var,negative_comments_var,neutral_comments_var)
        
        # Get video details
        video_details = sa.get_video_details(youtube_url)

        print(f"Positive count in views: {positive_count}")
        #Percentage count for the chart
        pos_percentage = math.ceil((positive_count/total) * 100)
        neg_percentage = math.ceil((negative_count/total) * 100)
        neu_percentage = math.ceil((neutral_count/total) * 100)

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