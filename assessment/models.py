from django.db import models
from django.contrib.auth.models import User


class SkillAssessment(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    programming_languages = models.TextField(blank=True)
    frameworks = models.TextField(blank=True)
    databases = models.TextField(blank=True)
    tools = models.TextField(blank=True)

    career_goal = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Skill Assessment"