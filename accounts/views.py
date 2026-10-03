from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from .forms import RegisterForm, EditProfileForm
from django.contrib.auth.models import User
from .models import Skill, CareerPath, LearningRoadmap

from assessment.models import (
    SkillAssessment,
    AssessmentResult,
)

from ai_engine.models import GeneratedRoadmap

from roadmap.models import (
    RoadmapAssessment,
    RoadmapAssessmentAttempt,
)

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

    # =====================================================
    # BASIC PLATFORM COUNTS
    # =====================================================

    students = User.objects.filter(
        is_staff=False,
        is_superuser=False
    )

    students_count = students.count()

    skills_count = Skill.objects.filter(
        is_active=True
    ).count()

    career_paths_count = CareerPath.objects.filter(
        is_active=True
    ).count()

    assessment_count = AssessmentResult.objects.filter(
        user__in=students
    ).count()

    roadmaps = GeneratedRoadmap.objects.filter(
        user__in=students,
        is_active=True
    )

    roadmaps_count = roadmaps.count()


    # =====================================================
    # COMPLETED ROADMAPS
    # =====================================================

    completed_roadmaps = 0

    for roadmap in roadmaps:

        phases = roadmap.roadmap_data.get(
            "phases",
            []
        )

        total_phases = len(phases)

        if total_phases == 0:
            continue

        completed_phases = RoadmapAssessment.objects.filter(
            roadmap=roadmap,
            is_completed=True
        ).values(
            "phase_number"
        ).distinct().count()

        progress = round(
            (completed_phases / total_phases) * 100
        )

        if progress == 100:
            completed_roadmaps += 1


    # =====================================================
    # ASSESSMENT ANALYTICS
    # =====================================================

    assessed_students = AssessmentResult.objects.filter(
        user__in=students
    ).values(
        "user"
    ).distinct().count()

    assessment_completion = 0

    if students_count > 0:

        assessment_completion = round(
            (
                assessed_students /
                students_count
            ) * 100
        )


    # =====================================================
    # ROADMAP STARTED
    # =====================================================

    roadmap_started_students = 0

    for roadmap in roadmaps:

        has_attempt = RoadmapAssessmentAttempt.objects.filter(
            assessment__roadmap=roadmap,
            user=roadmap.user
        ).exists()

        if has_attempt:
            roadmap_started_students += 1


    roadmap_started_percentage = 0

    if students_count > 0:

        roadmap_started_percentage = round(
            (
                roadmap_started_students /
                students_count
            ) * 100
        )


    # =====================================================
    # ROADMAP COMPLETION
    # =====================================================

    roadmap_completion_percentage = 0

    if roadmaps_count > 0:

        roadmap_completion_percentage = round(
            (
                completed_roadmaps /
                roadmaps_count
            ) * 100
        )


    # =====================================================
    # LEARNING STATUS
    # =====================================================

    completed_percentage = roadmap_completion_percentage

    students_with_roadmap = roadmaps.values(
        "user"
    ).distinct().count()

    in_progress_students = max(
        students_with_roadmap -
        completed_roadmaps,
        0
    )

    in_progress_percentage = 0

    if students_count > 0:

        in_progress_percentage = round(
            (
                in_progress_students /
                students_count
            ) * 100
        )


    not_started_percentage = max(
        100 -
        completed_percentage -
        in_progress_percentage,
        0
    )


    # =====================================================
    # POPULAR CAREER PATHS
    # =====================================================

    career_path_data = []

    career_paths = CareerPath.objects.filter(
        is_active=True
    )

    for career in career_paths:

        count = SkillAssessment.objects.filter(
            user__in=students,
            career_path=career
        ).count()

        if count > 0:

            career_path_data.append({
                "name": career.name,
                "count": count,
            })


    career_path_data.sort(
        key=lambda item: item["count"],
        reverse=True
    )

    career_path_data = career_path_data[:5]


    # =====================================================
    # CAREER BAR PERCENTAGES
    # =====================================================

    max_career_count = 0

    if career_path_data:

        max_career_count = max(
            item["count"]
            for item in career_path_data
        )

    for item in career_path_data:

        if max_career_count > 0:

            item["percentage"] = round(
                (
                    item["count"] /
                    max_career_count
                ) * 100
            )

        else:

            item["percentage"] = 0


    # =====================================================
    # RECENT STUDENTS
    # =====================================================

    recent_students = students.order_by(
        "-date_joined"
    )[:5]


    # =====================================================
    # RECENT ASSESSMENTS
    # =====================================================

    recent_assessments = AssessmentResult.objects.filter(
        user__in=students
    ).select_related(
        "user"
    ).order_by(
        "-completed_at"
    )[:5]


    # =====================================================
    # RECENT ROADMAPS
    # =====================================================

    recent_roadmaps = GeneratedRoadmap.objects.filter(
        user__in=students
    ).select_related(
        "user"
    ).order_by(
        "-created_at"
    )[:5]


    # =====================================================
    # AI LEARNING INSIGHT
    # =====================================================

    ai_insight = None

    if career_path_data:

        popular_career = career_path_data[0]

        ai_insight = {
            "title": "Most Selected Career Path",

            "career": popular_career["name"],

            "count": popular_career["count"],

            "description": (
                f"{popular_career['count']} student"
                f"{'s' if popular_career['count'] != 1 else ''} "
                f"currently selected "
                f"{popular_career['name']}."
            ),
        }


    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "students_count":
            students_count,

        "skills_count":
            skills_count,

        "career_paths_count":
            career_paths_count,

        "assessment_count":
            assessment_count,

        "roadmaps_count":
            roadmaps_count,

        "completed_roadmaps":
            completed_roadmaps,

        "assessment_completion":
            assessment_completion,

        "roadmap_started_percentage":
            roadmap_started_percentage,

        "roadmap_completion_percentage":
            roadmap_completion_percentage,

        "completed_percentage":
            completed_percentage,

        "in_progress_percentage":
            in_progress_percentage,

        "not_started_percentage":
            not_started_percentage,

        "career_path_data":
            career_path_data,

        "recent_students":
            recent_students,

        "recent_assessments":
            recent_assessments,

        "recent_roadmaps":
            recent_roadmaps,

        "ai_insight":
            ai_insight,
    }


    return render(
        request,
        "admin_dashboard.html",
        context
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