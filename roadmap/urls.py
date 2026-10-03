from django.urls import path
from . import views
app_name = "roadmap"
urlpatterns = [

    path(
        "topic/<int:progress_id>/start/",
        views.start_topic,
        name="start_topic"
    ),

    path(
        "topic/<int:progress_id>/complete/",
        views.complete_topic,
        name="complete_topic"
    ),

    path(
        "assessment/<int:phase_number>/",
        views.start_roadmap_assessment,
        name="start_roadmap_assessment"
    ),

    path(
        "assessment/result/<int:attempt_id>/",
        views.roadmap_assessment_result,
        name="roadmap_assessment_result"
    ),

    path(
        "progress/",
        views.my_progress,
        name="my_progress"
    ),
]