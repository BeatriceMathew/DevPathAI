from django.db import models
from django.contrib.auth.models import User


class SkillAssessment(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    programming_languages = models.TextField(blank=True)
    frameworks = models.TextField(blank=True)
    databases = models.TextField(blank=True)
    tools = models.TextField(blank=True)

    career_goal = models.CharField(max_length=100, blank=True)

    career_path = models.ForeignKey(
        "accounts.CareerPath",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_assessments"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Skill Assessment"

class AssessmentQuestion(models.Model):

    CATEGORY_CHOICES = [
        ("programming", "Programming"),
        ("frameworks", "Frameworks"),
        ("databases", "Databases"),
        ("tools", "Tools"),
    ]

    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    question = models.TextField()

    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)

    correct_answer = models.CharField(
        max_length=1,
        choices=[
            ("A", "Option A"),
            ("B", "Option B"),
            ("C", "Option C"),
            ("D", "Option D"),
        ]
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default="medium"
    )

    # NEW
    skill = models.ForeignKey(
        "accounts.Skill",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assessment_questions"
    )

    # NEW
    career_paths = models.ManyToManyField(
        "accounts.CareerPath",
        blank=True,
        related_name="assessment_questions"
    )

    def __str__(self):
        return self.question

class AssessmentResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    percentage = models.FloatField(default=0)
    completed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.score}/{self.total_questions}"

class AssessmentAnswer(models.Model):
    result = models.ForeignKey(
        AssessmentResult,
        on_delete=models.CASCADE,
        related_name="answers"
    )

    question = models.ForeignKey(
        AssessmentQuestion,
        on_delete=models.CASCADE
    )

    selected_answer = models.CharField(
        max_length=1,
        blank=True
    )

    is_correct = models.BooleanField(
        default=False
    )

    class Meta:
        unique_together = ("result", "question")

    def __str__(self):
        return f"{self.result.user.username} - Question {self.question.id}"

class SkillAssessmentResult(models.Model):
    LEVEL_CHOICES = [
        ("Beginner", "Beginner"),
        ("Intermediate", "Intermediate"),
        ("Advanced", "Advanced"),
        ("Expert", "Expert"),
    ]

    result = models.ForeignKey(
        AssessmentResult,
        on_delete=models.CASCADE,
        related_name="skill_results"
    )

    skill = models.ForeignKey(
        "accounts.Skill",
        on_delete=models.CASCADE,
        related_name="assessment_results"
    )

    correct_answers = models.PositiveIntegerField(default=0)

    total_questions = models.PositiveIntegerField(default=0)

    percentage = models.FloatField(default=0)

    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default="Beginner"
    )

    class Meta:
        unique_together = ("result", "skill")
        ordering = ["skill__name"]

    def __str__(self):
        return (
            f"{self.result.user.username} - "
            f"{self.skill.name} - {self.level}"
        )

    