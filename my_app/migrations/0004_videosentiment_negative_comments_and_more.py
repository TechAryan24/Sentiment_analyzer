# Generated by Django 5.1.1 on 2024-10-18 20:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('my_app', '0003_videosentiment'),
    ]

    operations = [
        migrations.AddField(
            model_name='videosentiment',
            name='negative_comments',
            field=models.TextField(default='[]'),
        ),
        migrations.AddField(
            model_name='videosentiment',
            name='positive_comments',
            field=models.TextField(default='[]'),
        ),
    ]
