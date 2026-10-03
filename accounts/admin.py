from django.contrib import admin
from .models import (
    Skill,
    CareerPath,
    CareerSkill,
    LearningRoadmap,
    RoadmapTopic,
)


@admin.register(RoadmapTopic)
class RoadmapTopicAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "roadmap",
        "skill",
        "order",
        "estimated_hours",
        "is_active",
    )

    list_filter = (
        "roadmap",
        "skill",
        "is_active",
    )

    search_fields = (
        "title",
        "description",
        "roadmap__title",
        "skill__name",
    )

    ordering = (
        "roadmap",
        "order",
    )