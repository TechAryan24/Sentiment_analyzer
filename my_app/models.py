from django.db import models
import json

# Create your models here.

class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.email

# Model for storing video data
class VideoSentiment(models.Model):
    video_id = models.CharField(max_length=255, unique=True)  # Store the unique video ID
    positive_count = models.IntegerField()
    negative_count = models.IntegerField()
    neutral_count = models.IntegerField()
    gen_description = models.TextField()
    result = models.TextField()
    positive_comments = models.TextField(default="[]")  # Default empty list as string
    negative_comments = models.TextField(default="[]")   # Field to store serialized negative comments
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sentiment Analysis for Video {self.video_id}"

    # Add methods to serialize and deserialize the comments
    def set_positive_comments(self, comments_list):
        self.positive_comments = json.dumps(comments_list)

    def get_positive_comments(self):
        return json.loads(self.positive_comments)

    def set_negative_comments(self, comments_list):
        self.negative_comments = json.dumps(comments_list)

    def get_negative_comments(self):
        return json.loads(self.negative_comments)