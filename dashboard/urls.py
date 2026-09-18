from django.urls import path
from . import views


urlpatterns = [

    path(
        "",
        views.dashboard,
        name="dashboard"
    ),

    path(
        "profile/",
        views.student_profile,
        name="student_profile"
    ),

    path(
        "change-password/",
        views.change_password,
        name="change_password"
    ),
]