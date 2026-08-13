from django.urls import path
from . import views


urlpatterns = [

    path(
        "register/",
        views.register,
        name="register"
    ),

    path(
        "login/",
        views.user_login,
        name="login"
    ),

    path(
            "logout/",
            views.user_logout,
            name="logout"
        ),


    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard"
    ),

    path(
        "admin-profile/",
        views.admin_profile,
        name="admin_profile"
    ),

    path(
        "students/",
        views.students_list,
        name="students_list"
    ),

    path(
    "students/delete/<int:student_id>/",
    views.delete_student,
    name="delete_student"
    ),

    path(
    "edit-profile/",
    views.edit_profile,
    name="edit_profile"
    ),


]