from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .forms import RegisterForm, EditProfileForm
from django.contrib.auth.models import User
from .models import Skill, CareerPath, LearningRoadmap

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

@login_required
def admin_dashboard(request):

    students_count = User.objects.filter(
        is_staff=False,
        is_superuser=False
    ).count()

    skills_count = Skill.objects.filter(
        is_active=True
    ).count()

    return render(
        request,
        "admin_dashboard.html",
        {
            "students_count": students_count,
            "skills_count": skills_count,
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



@login_required
def students_list(request):

    # Active students
    active_students = User.objects.filter(
        is_active=True,
        is_staff=False
    ).order_by('-date_joined')

    # Inactive students
    inactive_students = User.objects.filter(
        is_active=False,
        is_staff=False
    ).order_by('-date_joined')

    # Which list should be displayed?
    status = request.GET.get('status', 'active')

    if status == 'inactive':
        students = inactive_students
    else:
        students = active_students
        status = 'active'

    context = {
        'students': students,
        'active_students_count': active_students.count(),
        'inactive_students_count': inactive_students.count(),
        'current_status': status,
    }

    return render(
        request,
        'accounts/students.html',
        context
    )


@login_required
def delete_student(request, student_id):

    student = get_object_or_404(
        User,
        id=student_id,
        is_staff=False
    )

    if request.method == 'POST':

        # Do NOT permanently delete the student.
        # Deactivate the account instead.
        student.is_active = False
        student.save()

        return redirect(
            'students_list'
        )

    return render(
        request,
        'accounts/delete_student.html',
        {
            'student': student
        }
    )


@login_required
def restore_student(request, student_id):

    student = get_object_or_404(
        User,
        id=student_id,
        is_staff=False
    )

    if request.method == 'POST':

        student.is_active = True
        student.save()

        return redirect(
            'students_list'
        )

    return redirect('students_list')

@login_required
def student_detail(request, student_id):

    student = get_object_or_404(
        User,
        id=student_id,
        is_staff=False
    )

    return render(
        request,
        "accounts/student_detail.html",
        {
            "student": student
        }
    )

# ==============================
# LOGOUT
# ==============================

def user_logout(request):

    logout(request)

    return redirect("home")

# ==============================
# Skills Management page
# ==============================

@login_required
def skills_list(request):

    active_skills = Skill.objects.filter(
        is_active=True
    ).order_by('name')

    inactive_skills = Skill.objects.filter(
        is_active=False
    ).order_by('name')

    status = request.GET.get('status', 'active')

    if status == 'inactive':
        skills = inactive_skills
    else:
        skills = active_skills
        status = 'active'

    context = {
        'skills': skills,
        'active_skills_count': active_skills.count(),
        'inactive_skills_count': inactive_skills.count(),
        'current_status': status,
    }

    return render(
        request,
        'accounts/skills.html',
        context
    )
@login_required
def add_skill(request):

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if not name:
            return render(
                request,
                "accounts/add_skill.html",
                {
                    "error": "Skill name is required.",
                    "name": name,
                    "description": description,
                }
            )

        if Skill.objects.filter(
            name__iexact=name
        ).exists():

            return render(
                request,
                "accounts/add_skill.html",
                {
                    "error": "This skill already exists.",
                    "name": name,
                    "description": description,
                }
            )

        Skill.objects.create(
            name=name,
            description=description,
            is_active=True
        )

        return redirect("skills_list")

    return render(
        request,
        "accounts/add_skill.html"
    )

@login_required
def edit_skill(request, skill_id):

    skill = get_object_or_404(
        Skill,
        id=skill_id
    )

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if not name:
            return render(
                request,
                "accounts/edit_skill.html",
                {
                    "skill": skill,
                    "error": "Skill name is required."
                }
            )

        # Check duplicate name
        duplicate = Skill.objects.filter(
            name__iexact=name
        ).exclude(
            id=skill.id
        ).exists()

        if duplicate:
            return render(
                request,
                "accounts/edit_skill.html",
                {
                    "skill": skill,
                    "error": "Another skill with this name already exists."
                }
            )

        skill.name = name
        skill.description = description

        skill.save()

        return redirect("skills_list")

    return render(
        request,
        "accounts/edit_skill.html",
        {
            "skill": skill
        }
    )

@login_required
def delete_skill(request, skill_id):

    skill = get_object_or_404(
        Skill,
        id=skill_id
    )

    # If already inactive, return to the skills page
    if not skill.is_active:
        return redirect("skills_list")

    if request.method == "POST":

        skill.is_active = False
        skill.save()

        return redirect(
            "skills_list"
        )

    return render(
        request,
        "accounts/delete_skill.html",
        {
            "skill": skill
        }
    )

@login_required
def restore_skill(request, skill_id):

    skill = get_object_or_404(
        Skill,
        id=skill_id
    )

    skill.is_active = True
    skill.save()

    return redirect(
        "skills_list"
    )

# ==============================
# Career Paths list view
# ==============================

@login_required
def career_paths_list(request):

    active_career_paths = CareerPath.objects.filter(
        is_active=True
    ).order_by("name")

    inactive_career_paths = CareerPath.objects.filter(
        is_active=False
    ).order_by("name")

    status = request.GET.get(
        "status",
        "active"
    )

    if status == "inactive":

        career_paths = inactive_career_paths

    else:

        career_paths = active_career_paths

        status = "active"

    context = {
        "career_paths": career_paths,

        "active_career_paths_count":
            active_career_paths.count(),

        "inactive_career_paths_count":
            inactive_career_paths.count(),

        "current_status": status,
    }

    return render(
        request,
        "accounts/career_paths.html",
        context
    )

@login_required
def add_career_path(request):

    skills = Skill.objects.filter(
        is_active=True
    ).order_by("name")

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        description = request.POST.get(
            "description",
            ""
        ).strip()

        selected_skill_ids = request.POST.getlist(
            "skills"
        )

        if not name:

            return render(
                request,
                "accounts/add_career_path.html",
                {
                    "skills": skills,
                    "name": name,
                    "description": description,
                    "selected_skill_ids":
                        selected_skill_ids,
                    "error":
                        "Career path name is required."
                }
            )

        # Check duplicate career path name
        duplicate = CareerPath.objects.filter(
            name__iexact=name
        ).exists()

        if duplicate:

            return render(
                request,
                "accounts/add_career_path.html",
                {
                    "skills": skills,
                    "name": name,
                    "description": description,
                    "selected_skill_ids":
                        selected_skill_ids,
                    "error":
                        "This career path already exists."
                }
            )

        career_path = CareerPath.objects.create(
            name=name,
            description=description,
            is_active=True
        )

        # Assign selected skills
        selected_skills = Skill.objects.filter(
            id__in=selected_skill_ids,
            is_active=True
        )

        career_path.skills.set(
            selected_skills
        )

        return redirect(
            "career_paths_list"
        )

    return render(
        request,
        "accounts/add_career_path.html",
        {
            "skills": skills
        }
    )

@login_required   
def edit_career_path(request, career_path_id):

    career_path = get_object_or_404(
        CareerPath,
        id=career_path_id
    )

    skills = Skill.objects.filter(
        is_active=True
    ).order_by("name")

    if request.method == "POST":

        name = request.POST.get(
            "name",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        selected_skill_ids = request.POST.getlist(
            "skills"
        )

        if not name:

            return render(
                request,
                "accounts/edit_career_path.html",
                {
                    "career_path": career_path,
                    "skills": skills,
                    "selected_skill_ids": selected_skill_ids,
                    "error": "Career path name is required."
                }
            )

        duplicate = CareerPath.objects.filter(
            name__iexact=name
        ).exclude(
            id=career_path.id
        ).exists()

        if duplicate:

            return render(
                request,
                "accounts/edit_career_path.html",
                {
                    "career_path": career_path,
                    "skills": skills,
                    "selected_skill_ids": selected_skill_ids,
                    "error":
                        "Another career path with this name already exists."
                }
            )

        career_path.name = name
        career_path.description = description

        career_path.save()

        selected_skills = Skill.objects.filter(
            id__in=selected_skill_ids,
            is_active=True
        )

        career_path.skills.set(
            selected_skills
        )

        return redirect(
            "career_paths_list"
        )

    selected_skill_ids = list(
        career_path.skills.values_list(
            "id",
            flat=True
        )
    )

    return render(
        request,
        "accounts/edit_career_path.html",
        {
            "career_path": career_path,
            "skills": skills,
            "selected_skill_ids": selected_skill_ids,
        }
    )

@login_required
def delete_career_path(request, career_path_id):

    career_path = get_object_or_404(
        CareerPath,
        id=career_path_id
    )

    if not career_path.is_active:
        return redirect("career_paths_list")

    if request.method == "POST":

        career_path.is_active = False
        career_path.save()

        return redirect("career_paths_list")

    return render(
        request,
        "accounts/delete_career_path.html",
        {
            "career_path": career_path
        }
    )

@login_required
def restore_career_path(request, career_path_id):

    career_path = get_object_or_404(
        CareerPath,
        id=career_path_id
    )

    career_path.is_active = True
    career_path.save()

    return redirect("career_paths_list")

@login_required
def learning_roadmaps_list(request):

    current_status = request.GET.get(
        "status",
        "active"
    )

    active_count = LearningRoadmap.objects.filter(
        is_active=True
    ).count()

    inactive_count = LearningRoadmap.objects.filter(
        is_active=False
    ).count()

    if current_status == "inactive":

        roadmaps = LearningRoadmap.objects.filter(
            is_active=False
        ).select_related(
            "career_path"
        ).order_by("-created_at")

    else:

        current_status = "active"

        roadmaps = LearningRoadmap.objects.filter(
            is_active=True
        ).select_related(
            "career_path"
        ).order_by("-created_at")

    return render(
        request,
        "accounts/learning_roadmaps.html",
        {
            "roadmaps": roadmaps,
            "active_roadmaps_count": active_count,
            "inactive_roadmaps_count": inactive_count,
            "current_status": current_status,
        }
    )

@login_required
def add_learning_roadmap(request):

    career_paths = CareerPath.objects.filter(
        is_active=True
    ).order_by("name")

    if request.method == "POST":

        title = request.POST.get(
            "title",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        career_path_id = request.POST.get(
            "career_path"
        )

        duration = request.POST.get(
            "duration",
            ""
        ).strip()

        difficulty = request.POST.get(
            "difficulty",
            "Beginner"
        )

        if not title:

            return render(
                request,
                "accounts/add_learning_roadmap.html",
                {
                    "career_paths": career_paths,
                    "error":
                        "Roadmap title is required."
                }
            )

        if not career_path_id:

            return render(
                request,
                "accounts/add_learning_roadmap.html",
                {
                    "career_paths": career_paths,
                    "error":
                        "Please select a career path."
                }
            )

        career_path = get_object_or_404(
            CareerPath,
            id=career_path_id,
            is_active=True
        )

        duplicate = LearningRoadmap.objects.filter(
            title__iexact=title
        ).exists()

        if duplicate:

            return render(
                request,
                "accounts/add_learning_roadmap.html",
                {
                    "career_paths": career_paths,
                    "error":
                        "A roadmap with this title already exists."
                }
            )

        LearningRoadmap.objects.create(
            title=title,
            description=description,
            career_path=career_path,
            duration=duration,
            difficulty=difficulty
        )

        return redirect(
            "learning_roadmaps_list"
        )

    return render(
        request,
        "accounts/add_learning_roadmap.html",
        {
            "career_paths": career_paths
        }
    )

@login_required
def edit_learning_roadmap(request, roadmap_id):

    roadmap = get_object_or_404(
        LearningRoadmap,
        id=roadmap_id
    )

    career_paths = CareerPath.objects.filter(
        is_active=True
    ).order_by("name")

    if request.method == "POST":

        title = request.POST.get(
            "title",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        career_path_id = request.POST.get(
            "career_path"
        )

        duration = request.POST.get(
            "duration",
            ""
        ).strip()

        difficulty = request.POST.get(
            "difficulty",
            "Beginner"
        )

        if not title:

            return render(
                request,
                "accounts/edit_learning_roadmap.html",
                {
                    "roadmap": roadmap,
                    "career_paths": career_paths,
                    "error":
                        "Roadmap title is required."
                }
            )

        if not career_path_id:

            return render(
                request,
                "accounts/edit_learning_roadmap.html",
                {
                    "roadmap": roadmap,
                    "career_paths": career_paths,
                    "error":
                        "Please select a career path."
                }
            )

        career_path = get_object_or_404(
            CareerPath,
            id=career_path_id,
            is_active=True
        )

        duplicate = LearningRoadmap.objects.filter(
            title__iexact=title
        ).exclude(
            id=roadmap.id
        ).exists()

        if duplicate:

            return render(
                request,
                "accounts/edit_learning_roadmap.html",
                {
                    "roadmap": roadmap,
                    "career_paths": career_paths,
                    "error":
                        "Another roadmap with this title already exists."
                }
            )

        roadmap.title = title
        roadmap.description = description
        roadmap.career_path = career_path
        roadmap.duration = duration
        roadmap.difficulty = difficulty

        roadmap.save()

        return redirect(
            "learning_roadmaps_list"
        )

    return render(
        request,
        "accounts/edit_learning_roadmap.html",
        {
            "roadmap": roadmap,
            "career_paths": career_paths
        }
    )

@login_required
def deactivate_learning_roadmap(request, roadmap_id):

    roadmap = get_object_or_404(
        LearningRoadmap,
        id=roadmap_id
    )

    if request.method == "POST":

        roadmap.is_active = False
        roadmap.save()

        return redirect(
            "learning_roadmaps_list"
        )

    return render(
        request,
        "accounts/deactivate_learning_roadmap.html",
        {
            "roadmap": roadmap
        }
    )

@login_required
def restore_learning_roadmap(request, roadmap_id):

    roadmap = get_object_or_404(
        LearningRoadmap,
        id=roadmap_id
    )

    if request.method == "POST":

        roadmap.is_active = True
        roadmap.save()

        return redirect(
            "learning_roadmaps_list"
        )

    return render(
        request,
        "accounts/restore_learning_roadmap.html",
        {
            "roadmap": roadmap
        }
    )