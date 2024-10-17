import requests
from django.shortcuts import render
from django.http import JsonResponse
import os
import google.generativeai as genai
from googleapiclient.discovery import build
import csv
import re
from datetime import datetime
import ast # For safely parsing the list format

# API keys
YOUTUBE_API_KEY = "AIzaSyCcSLso25utXidUPntTdk4IFS6SPZihEXQ"
genai.configure(api_key="AIzaSyC3mUf8_GyYueas_mFlhymL5fYsUL_hdU0")

# Build the YouTube service
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

############ Logic for YouTube comment fetching  #####################

def analyze_comments(youtube_url):
    video_id = youtube_url.split("v=")[-1].split("&")[0]
    i = 1
    comments = []
    url = f'https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults=500&key={YOUTUBE_API_KEY}'
    
    while url:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error fetching comments: {response.status_code} - {response.text}")
            break

        data = response.json()
        for item in data.get('items', []):
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)
            i += 1
        print(f"Collected {len(comments)} comments so far")

        next_page_token = data.get('nextPageToken')
        if next_page_token:
            url = f'https://www.googleapis.com/youtube/v3/commentThreads?part=snippet&videoId={video_id}&maxResults=500&pageToken={next_page_token}&key={YOUTUBE_API_KEY}'
        else:
            print("No more comments to fetch.")
            url = None

    related_comments = filter_related_comments(comments)
    with open('my_app/csv/youtube_comments.csv', 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Comment'])
        for comment in related_comments:
            csvwriter.writerow([comment])
    
    print(f" Length of filtered comment: {len(related_comments)} ")
    return related_comments

def filter_related_comments(comments):
    related_comments = []
    for comment in comments:
        if is_related(comment):
            related_comments.append(comment)
    return related_comments

def is_related(comment):
    comment = comment.strip()
    if not comment or comment == "":
        return False
    if re.search(r'http[s]?://', comment):
        return False
    if re.search(r'[<>@#$%^&*{}()~`\[\]|\\/]', comment):
        return False
    if re.search(r'\d{1,2}:\d{2}', comment):
        return False
    if re.search(r'[\U00010000-\U0010ffff]', comment):
        return False
    if comment.isdigit():
        return False
    if len(comment.split()) == 1:
        return False
    if re.search(r'[^\x00-\x7F]', comment):
        return False
    return True

# Example usage
# youtube_url = "https://www.youtube.com/watch?v=tb37SwBvRoQ"
# comments = analyze_comments(youtube_url)

################### Establishing Gemini API ########################

generation_config = {
  "temperature": 0,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
)

chat_session = model.start_chat(
  history=[]
)

######################## Extracting keywords from description ###################


def gen_keyword(Description):
    keywords = []
    keyword_response = chat_session.send_message(f"""
    You are an intelligent text analyzer. I will provide you with a description. Your task is to extract the most important keywords that represent the core ideas or topics mentioned in the description.

    - Do not include common words (like "is", "the", "a", etc.).
    - Focus on nouns, verbs, and adjectives that are crucial for understanding the description.
    - The keywords should be in one word only.
    - Return only the keywords in the format: ["keyword1", "keyword2", "keyword3"]

    Here is the description: {Description}
    """)

    keyword_response_text = keyword_response.text

    # Convert the returned text into an actual Python list
    try:
        keywords = ast.literal_eval(keyword_response_text.strip())
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing the keyword response: {e}")

    return keywords
    print(f"keywords are: {keywords}")

###################### Filtering Unrelevant comments to the video ###################

def filtering(comments, keywords):
    rel_response = chat_session.send_message(f"""
    You are a highly accurate and detail-oriented text analyzer. I will provide you with a list of comments and user-specified keywords related to a video. Your task is to analyze these comments and determine their relevance to the provided keywords.

    1. For each comment, check if it relates to any of the keywords provided.
    2. If a comment is related to any of the keywords, categorize it as "relevant."
    3. If a comment does not relate to the keywords, categorize it as "not relevant."

    Please return the results as a Python list of lists, where each inner list contains two elements: 
    1. The comment (as a string).
    2. The relevance status ("relevant" or "not relevant").

    Ensure the output format is strictly followed. 

    Here are the keywords: {keywords}
    Here are the comments:
    {comments}

    """)

    rel_response_text = rel_response.text
    print (f"Without error response: { rel_response_text}")
    # Clean up the response text
    cleaned_text = rel_response_text.strip()  # Remove leading/trailing whitespace
    cleaned_text = cleaned_text.replace("```python", "").replace("```", "")  # Remove code block formatting

    
 # Ensure the response is a properly formatted list
    if not cleaned_text.startswith("[") or not cleaned_text.endswith("]"):
        cleaned_text = "[" + cleaned_text + "]" + "]" # Add brackets if missing
    
    # Initialize an array to store relevant comments
    relevant_comments = []

    try:
        # Safely evaluate the cleaned text as a Python list
        lines = ast.literal_eval(cleaned_text)
        
        for line_content in lines:
            # Check if the line_content is a list of length 2
            if isinstance(line_content, list) and len(line_content) == 2:
                comment, keyword_match = line_content
                # Store only the relevant comments
                if keyword_match.lower() == "relevant":
                    relevant_comments.append(comment)
    except (ValueError, SyntaxError) as e:
        print(f"Error in filtering: {e}") 
        # print(f"Raw response text: {cleaned_text}")  # Debug output of the raw response

    # Output the relevant comments
    print(f"Relevant comments: {len(relevant_comments)}")

    with open('my_app/csv/relevant_comments.csv', 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Relevant-Comment'])
        for comment in relevant_comments:
            csvwriter.writerow([comment])
    
    return relevant_comments



################### Logic to analyze the comments #####################3

def analyse_sentiment(relevant_comments):
    response = chat_session.send_message(f"""
    Determine the sentiment polarity of the comments from the options ["positive", "negative", "neutral"]. Answer in the format ["comment", "sentiment"] without any explanation. And make sure all the brackets are closed properly.
    {relevant_comments}
    """)

    # Process response and count sentiments
    response_text = response.text
    positive_comments = []
    negative_comments = []
    neutral_comments = []
    positive_count = 0
    negative_count = 0
    neutral_count = 0

    cleaned_text = response_text.strip()  # Remove leading/trailing whitespace
    cleaned_text = cleaned_text.replace("```python", "").replace("```", "") 

    try:
        # Safely evaluate the cleaned text as a Python list
        lines = ast.literal_eval(cleaned_text)
        
        for line_content in lines:
            # Check if the line_content is a list of length 2
            if isinstance(line_content, list) and len(line_content) == 2:
                comment, sentiment = line_content
                # Categorize the comments based on sentiment
                if sentiment == "positive":
                    positive_comments.append(comment)
                    positive_count += 1
                elif sentiment == "negative":
                    negative_comments.append(comment)
                    negative_count += 1
                elif sentiment == "neutral":
                    neutral_comments.append(comment)
                    neutral_count += 1
                        
    except (ValueError, SyntaxError) as e:
        print(f"Error parsing response: {e}")
        # print(f"Response text: {cleaned_text}")
        line_content = None 

    # Output the results
    print(f"Positive comments: {positive_count}")
    print(f"Negative comments: {negative_count}")
    print(f"Neutral comments: {neutral_count}")

    # Store comments in variables
    positive_comments_var = positive_comments
    negative_comments_var = negative_comments
    neutral_comments_var = neutral_comments

    with open('my_app/csv/positive_comments.csv', 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Positive-Comment'])
            for comment in positive_comments_var:
                csvwriter.writerow([comment])

    with open('my_app/csv/negative_comments.csv', 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Negative-Comment'])
            for comment in negative_comments_var:
                csvwriter.writerow([comment])

    with open('my_app/csv/neutral_comments.csv', 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['Neutral-Comment'])
            for comment in neutral_comments_var:
                csvwriter.writerow([comment])

    # Return the counts and positive comments
    return positive_count, negative_count, neutral_count, positive_comments_var,negative_comments_var,neutral_comments_var

############### Logic to generate the description ################
def gen_desc(positive_count, negative_count, neutral_count, positive_comments_var,negative_comments_var,neutral_comments_var):
    description_response = None  
    description_text = None
    result = "No conclusion can be drawn."  # Default result

    try: 
        if(positive_count > negative_count and positive_count > neutral_count):
            description_response = chat_session.send_message(f"""
            You are an advanced text generation model. I have a list of positive comments about a video, and I need you to create a compelling description that informs users why this video is worth watching. 
            Here are the positive comments:
            {positive_comments_var}
            Based on these comments, please generate a short description highlighting the key reasons users found this video enjoyable or valuable. The description should be engaging and encourage others to watch the video.
            """)
            result = "It’s definitely worth checking out."
            
        elif (negative_count > positive_count and negative_count > neutral_count):
            description_response = chat_session.send_message(f"""
            You are an advanced text generation model. I have a list of negative comments about a video, and I need you to create a concise description that informs users about the potential drawbacks or issues mentioned. 

            Here are the negative comments:
            {negative_comments_var}

            Based on these comments, please generate a brief description highlighting the key reasons users found this video disappointing or unsatisfactory. The description should be honest and help potential viewers make an informed decision about whether to watch the video.
            """)
            result = "It’s not worth the time to watch."

        elif (neutral_count > negative_count and neutral_count > positive_count):
            description_response = chat_session.send_message(f"""
            You are an advanced text generation model. I have a list of neutral comments about a video, and I need you to create a balanced and objective description based on these comments.

            Here are the neutral comments:
            {neutral_comments_var}

            Based on these comments, please generate a brief description that provides a fair and unbiased overview of the video. Highlight the key points mentioned by

            """)
            result = "It’s up to you whether you want to watch it or not"

        if description_response:
            description_text = description_response.text  # Capture the generated description
            print(f"Generated Description: {description_text}")
        else:
            print("No description generated. Please check the counts and conditions.")
            
    except StopCandidateException as e:
        print(f"Error: {e}")
        description_text = "Unable to generate a description due to content safety concerns."
        result = "Content flagged by the API."

    return description_text,result

############## Video details ###############

# def get_video_details(youtube_url):

#     video_id = youtube_url.split("v=")[-1].split("&")[0]
    
#     # Make a request to the YouTube API to get video details
#     request = youtube.videos().list(
#         part="snippet,statistics",  # We need snippet for metadata and statistics for views, likes, etc.
#         id=video_id
#     )
#     response = request.execute()

#     if not response['items']:
#         return None  # No video found with this ID

#     video_data = response['items'][0]

#     # Extract the required details
#     published_at = video_data['snippet']['publishedAt']

#      # Convert ISO 8601 date to a readable format
#     published_at_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").date()
#     readable_date = published_at_date.strftime("%B %d, %Y")  # Example: September 13, 2024

#     # Extract the required details
#     video_details = {
#         'title': video_data['snippet']['title'],
#         'published_at': readable_date,
#         'views': video_data['statistics'].get('viewCount', '0'),
#         'likes': video_data['statistics'].get('likeCount', '0'),
#         'dislikes': video_data['statistics'].get('dislikeCount', '0'),
#         'comments': video_data['statistics'].get('commentCount', '0'),
#     }

#     return video_details



