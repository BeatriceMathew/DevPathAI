from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import RegisterForm, EditProfileForm
from django.contrib.auth.models import User

# ==============================
# STUDENT REGISTRATION
# ==============================

def register(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            login(request, user)

            return redirect("dashboard")

    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form}
    )


# ==============================
# STUDENT / ADMIN LOGIN
# ==============================

def user_login(request):

    # Already logged-in user
    if request.user.is_authenticated:

        if request.user.is_staff:
            return redirect("admin_dashboard")

        return redirect("dashboard")


    error = None


    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")
        role = request.POST.get("role")


        # Authenticate user
        user = authenticate(
            request,
            username=username,
            password=password
        )


        if user is not None:


            # ==============================
            # ADMIN LOGIN
            # ==============================

            if role == "admin":

                if user.is_staff:

                    login(request, user)

                    return redirect("admin_dashboard")

                else:

                    error = (
                        "You do not have administrator access."
                    )


            # ==============================
            # STUDENT LOGIN
            # ==============================

            elif role == "student":

                if not user.is_staff:

                    login(request, user)

                    return redirect("dashboard")

                else:

                    error = (
                        "Administrator accounts "
                        "cannot login as students."
                    )


            # ==============================
            # NO ROLE SELECTED
            # ==============================

            else:

                error = "Please select a login type."


        else:

            error = "Invalid username or password."


    return render(
        request,
        "accounts/login.html",
        {
            "error": error
        }
    )


# ==============================
# ADMIN DASHBOARD
# ==============================

def admin_dashboard(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_staff:
        return redirect("dashboard")

    students_count = User.objects.filter(
        is_staff=False
    ).count()

    return render(
        request,
        "admin_dashboard.html",
        {
            "students_count": students_count
        }
    )

def admin_profile(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_staff:
        return redirect("dashboard")

    return render(
        request,
        "accounts/admin_profile.html"
    )


def students_list(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_staff:
        return redirect("dashboard")

    students = User.objects.filter(is_staff=False).order_by("-date_joined")

    return render(
        request,
        "accounts/students.html",
        {
            "students": students
        }
    )

def delete_student(request, student_id):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_staff:
        return redirect("dashboard")

    student = User.objects.get(
        id=student_id,
        is_staff=False
    )

    if request.method == "POST":

        student.delete()

        return redirect("students_list")

    return render(
        request,
        "accounts/delete_student.html",
        {
            "student": student
        }
    )

def edit_profile(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_staff:
        return redirect("dashboard")

    if request.method == "POST":

        form = EditProfileForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():

            form.save()

            return redirect("admin_profile")

    else:

        form = EditProfileForm(
            instance=request.user
        )

    return render(
        request,
        "accounts/edit_profile.html",
        {
            "form": form
        }
    )

# ==============================
# LOGOUT
# ==============================

def user_logout(request):

    logout(request)

    return redirect("home")