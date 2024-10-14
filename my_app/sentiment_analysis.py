import requests
from django.shortcuts import render
from django.http import JsonResponse
import os
import google.generativeai as genai
import csv
import re
import ast # For safely parsing the list format

# API keys
YOUTUBE_API_KEY = "AIzaSyCcSLso25utXidUPntTdk4IFS6SPZihEXQ"
genai.configure(api_key="AIzaSyC3mUf8_GyYueas_mFlhymL5fYsUL_hdU0")

# Logic for YouTube comment fetching
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
youtube_url = "https://www.youtube.com/watch?v=tb37SwBvRoQ"
comments = analyze_comments(youtube_url)


# Logic to analyze the comments
generation_config = {
  "temperature": 0.0,
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

response = chat_session.send_message(f"""
 Determine the sentiment polarity of the comments from the options ["positive", "negative", "neutral"]. Answer in the format ["comment", "sentiment"] without any explanation.
{comments}
""")

# print(response.text)

# Process response and count sentiments
response_text = response.text
positive_comments = []
negative_comments = []
neutral_comments = []
positive_count = 0
negative_count = 0
neutral_count = 0

# Extract comments and sentiments
lines = response_text.split('\n')

for line in lines:
    line = line.strip()  # Remove any surrounding whitespace
    if line.startswith('[') and line.endswith(']'):
        try:
            # Safely evaluate the line as a Python list using ast.literal_eval
            line_content = ast.literal_eval(line)  # This will convert the string like ['comment', 'sentiment'] into a list
            
            # Ensure we have exactly two elements: the comment and the sentiment
            if len(line_content) == 2:
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
        except (ValueError, SyntaxError):
            # Handle any lines that don't conform to a valid list structure
            print(f"Skipping line due to parsing error: {line}")


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
