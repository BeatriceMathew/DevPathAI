from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views


urlpatterns = [

    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "",
        include("core.urls")
    ),

    path(
        "accounts/",
        include("accounts.urls")
    ),

    path(
        "dashboard/",
        include("dashboard.urls")
    ),

    path(
        "accounts/password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url="/accounts/password-changed/"
        ),
        name="password_change"
    ),

    path(
        "accounts/password-changed/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_changed.html"
        ),
        name="password_changed"
    ),

]