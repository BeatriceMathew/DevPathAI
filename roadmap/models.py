from django.db import models
from django.contrib.auth.models import User


class RoadmapTopicProgress(models.Model):

    STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="roadmap_topic_progress"
    )

    roadmap = models.ForeignKey(
        "ai_engine.GeneratedRoadmap",
        on_delete=models.CASCADE,
        related_name="topic_progress"
    )

    phase_number = models.PositiveIntegerField()

    topic = models.CharField(
        max_length=255
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="not_started"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        unique_together = (
            "roadmap",
            "phase_number",
            "topic"
        )

        ordering = [
            "phase_number",
            "id"
        ]

    def __str__(self):

        return (
            f"{self.user.username} - "
            f"Phase {self.phase_number} - "
            f"{self.topic}"
        )

class RoadmapAssessment(models.Model):

    roadmap = models.ForeignKey(
        "ai_engine.GeneratedRoadmap",
        on_delete=models.CASCADE,
        related_name="assessments"
    )

    phase_number = models.PositiveIntegerField()

    phase_title = models.CharField(
        max_length=255
    )

    questions = models.JSONField(
        default=list
    )

    passing_percentage = models.PositiveIntegerField(
        default=70
    )

    is_unlocked = models.BooleanField(
        default=False
    )

    is_completed = models.BooleanField(
        default=False
    )

    best_score = models.FloatField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        unique_together = (
            "roadmap",
            "phase_number"
        )

        ordering = [
            "phase_number"
        ]

    def __str__(self):

        return (
            f"{self.roadmap.user.username} - "
            f"Phase {self.phase_number} - "
            f"{self.phase_title}"
        )


class RoadmapAssessmentAttempt(models.Model):

    assessment = models.ForeignKey(
        RoadmapAssessment,
        on_delete=models.CASCADE,
        related_name="attempts"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="roadmap_assessment_attempts"
    )

    score = models.PositiveIntegerField(
        default=0
    )

    total_questions = models.PositiveIntegerField(
        default=0
    )

    percentage = models.FloatField(
        default=0
    )

    passed = models.BooleanField(
        default=False
    )

    answers = models.JSONField(
        default=list
    )

    completed_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = [
            "-completed_at"
        ]

    def __str__(self):

        return (
            f"{self.user.username} - "
            f"{self.assessment.phase_title} - "
            f"{self.percentage}%"
        )