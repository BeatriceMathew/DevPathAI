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
        "edit-profile/",
        views.edit_profile,
        name="edit_profile"
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
        'students/restore/<int:student_id>/',
        views.restore_student,
        name='restore_student'
    ),

    path(
    "students/view/<int:student_id>/",
    views.student_detail,
    name="student_detail"
    ),

    path(
    'skills/',
    views.skills_list,
    name='skills_list'
    ),

    path(
    "skills/add/",
    views.add_skill,
    name="add_skill"
    ),

   path(
    "skills/edit/<int:skill_id>/",
    views.edit_skill,
    name="edit_skill"
    ),

    path(
    "skills/delete/<int:skill_id>/",
    views.delete_skill,
    name="delete_skill"
    ),

    path(
    "skills/restore/<int:skill_id>/",
    views.restore_skill,
    name="restore_skill"
    ),

    path(
    "career-paths/",
    views.career_paths_list,
    name="career_paths_list"
    ),

    path(
    "career-paths/add/",
    views.add_career_path,
    name="add_career_path"
    ),

    path(
    "career-paths/edit/<int:career_path_id>/",
    views.edit_career_path,
    name="edit_career_path"
    ),

    path(
    "career-paths/delete/<int:career_path_id>/",
    views.delete_career_path,
    name="delete_career_path"
    ),

    path(
        "career-paths/restore/<int:career_path_id>/",
        views.restore_career_path,
        name="restore_career_path"
    ),

    path(
        "learning-roadmaps/",
        views.learning_roadmaps_list,
        name="learning_roadmaps_list"
    ),

    path(
        "learning-roadmaps/add/",
        views.add_learning_roadmap,
        name="add_learning_roadmap"
    ),

    path(
        "learning-roadmaps/edit/<int:roadmap_id>/",
        views.edit_learning_roadmap,
        name="edit_learning_roadmap"
    ),

    path(
        "learning-roadmaps/deactivate/<int:roadmap_id>/",
        views.deactivate_learning_roadmap,
        name="deactivate_learning_roadmap"
    ),

    path(
        "learning-roadmaps/restore/<int:roadmap_id>/",
        views.restore_learning_roadmap,
        name="restore_learning_roadmap"
    ),


]