from django.contrib import admin

# Register your models here.

from .models import User, VideoSentiment

admin.site.register(User)
admin.site.register(VideoSentiment)

