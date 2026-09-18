from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect


@login_required
def dashboard(request):
    return render(request, "dashboard/dashboard.html")


@login_required
def student_profile(request):

    if request.method == "POST":

        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()

        if not first_name:
            return render(
                request,
                "dashboard/student_profile.html",
                {
                    "error": "First name is required."
                }
            )

        if not email:
            return render(
                request,
                "dashboard/student_profile.html",
                {
                    "error": "Email address is required."
                }
            )

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email

        request.user.save()

        messages.success(
            request,
            "Your profile has been updated successfully."
        )

        return redirect("student_profile")

    return render(
        request,
        "dashboard/student_profile.html"
    )


@login_required
def change_password(request):

    if request.method == "POST":

        form = PasswordChangeForm(
            request.user,
            request.POST
        )

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(
                request,
                user
            )

            messages.success(
                request,
                "Your password has been changed successfully."
            )

            return redirect("student_profile")

    else:

        form = PasswordChangeForm(
            request.user
        )

    return render(
        request,
        "dashboard/change_password.html",
        {
            "form": form
        }
    )