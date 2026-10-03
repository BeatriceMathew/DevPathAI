from django.db import models
from django.contrib.auth.models import User


class GeneratedRoadmap(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="generated_roadmaps"
    )

    career = models.CharField(
        max_length=150
    )

    roadmap_data = models.JSONField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    is_active = models.BooleanField(
        default=True
    )

    def __str__(self):

        return f"{self.user.username} - {self.career}"