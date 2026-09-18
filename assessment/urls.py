from django.urls import path
from . import views

urlpatterns = [
    path(
        "",
        views.assessment,
        name="assessment"
    ),

    path(
    "admin/questions/",
    views.admin_assessment_questions,
    name="admin_assessment_questions"
    ),

    path(
        "admin/questions/add/",
        views.add_assessment_question,
        name="add_assessment_question"
    ),

    path(
    "admin/questions/<int:question_id>/edit/",
    views.edit_assessment_question,
    name="edit_assessment_question"
    ),

    path(
        "admin/questions/<int:question_id>/delete/",
        views.delete_assessment_question,
        name="delete_assessment_question"
    ),

    path("result/",
        views.assessment_result, 
        name="assessment_result"
    ),
]