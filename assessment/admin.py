from django.contrib import admin
from .models import SkillAssessment, AssessmentQuestion


@admin.register(SkillAssessment)
class SkillAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "career_goal",
        "created_at",
        "updated_at",
    )


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "question",
        "category",
        "correct_answer",
    )

    list_filter = ("category",)

    search_fields = ("question",)