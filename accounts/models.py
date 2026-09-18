from django.db import models


class Skill(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class CareerPath(models.Model):

    name = models.CharField(
        max_length=150,
        unique=True
    )

    description = models.TextField(
        blank=True
    )

    skills = models.ManyToManyField(
        Skill,
        related_name="career_paths",
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class CareerSkill(models.Model):

    LEVEL_CHOICES = [
        ("Beginner", "Beginner"),
        ("Intermediate", "Intermediate"),
        ("Advanced", "Advanced"),
        ("Expert", "Expert"),
    ]

    career_path = models.ForeignKey(
        CareerPath,
        on_delete=models.CASCADE,
        related_name="career_skills"
    )

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="career_requirements"
    )

    required_level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default="Beginner"
    )

    priority = models.PositiveIntegerField(
        default=1
    )

    is_required = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        unique_together = ("career_path", "skill")
        ordering = ["priority", "skill__name"]

    def __str__(self):
        return (
            f"{self.career_path.name} - "
            f"{self.skill.name} - "
            f"{self.required_level}"
        )


class LearningRoadmap(models.Model):

    title = models.CharField(
        max_length=150
    )

    description = models.TextField(
        blank=True
    )

    career_path = models.ForeignKey(
        CareerPath,
        on_delete=models.CASCADE,
        related_name="roadmaps"
    )

    duration = models.CharField(
        max_length=100,
        blank=True
    )

    difficulty = models.CharField(
        max_length=50,
        choices=[
            ("Beginner", "Beginner"),
            ("Intermediate", "Intermediate"),
            ("Advanced", "Advanced"),
        ],
        default="Beginner"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title