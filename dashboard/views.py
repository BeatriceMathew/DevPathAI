from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect
from roadmap.models import RoadmapAssessment, RoadmapAssessmentAttempt
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from accounts.models import CareerPath, CareerSkill
from assessment.models import (
    SkillAssessment,
    AssessmentResult,
    SkillAssessmentResult,
)
from ai_engine.models import GeneratedRoadmap
from roadmap.models import RoadmapAssessment, RoadmapAssessmentAttempt

@login_required
def dashboard(request):

    from assessment.models import (
        SkillAssessment,
        AssessmentResult,
        SkillAssessmentResult
    )
    from accounts.models import CareerSkill

    # -----------------------------------
    # Career goal
    # -----------------------------------

    assessment = SkillAssessment.objects.filter(
        user=request.user
    ).select_related("career_path").first()

    career_goal = None

    if assessment and assessment.career_path:
        career_goal = assessment.career_path

    # -----------------------------------
    # Assessment result
    # -----------------------------------

    assessment_result = AssessmentResult.objects.filter(
        user=request.user
    ).order_by("-completed_at").first()

    # -----------------------------------
    # Skill gap information
    # -----------------------------------

    skill_gaps = []
    priority_skill = None

    if assessment_result and career_goal:

        career_skills = CareerSkill.objects.filter(
            career_path=career_goal
        ).select_related("skill")

        skill_results = {
            item.skill_id: item
            for item in assessment_result.skill_results.select_related("skill")
        }

        level_order = {
            "Beginner": 1,
            "Intermediate": 2,
            "Advanced": 3,
            "Expert": 4
        }

        for career_skill in career_skills:

            student_result = skill_results.get(
                career_skill.skill_id
            )

            if student_result:
                current_level = student_result.level
                percentage = student_result.percentage
            else:
                current_level = "Beginner"
                percentage = 0

            required_level = career_skill.required_level

            current_value = level_order.get(
                current_level,
                1
            )

            required_value = level_order.get(
                required_level,
                1
            )

            gap = max(
                required_value - current_value,
                0
            )

            skill_gaps.append({
                "skill": career_skill.skill,
                "current_level": current_level,
                "required_level": required_level,
                "percentage": percentage,
                "gap": gap,
                "priority": career_skill.priority,
                "is_required": career_skill.is_required,
            })

        # Highest-priority skill that has a gap
        gap_skills = [
            item for item in skill_gaps
            if item["gap"] > 0
        ]

        gap_skills.sort(
            key=lambda item: item["priority"]
        )

        if gap_skills:
            priority_skill = gap_skills[0]


            # -----------------------------------
    # AI Roadmap Progress
    # -----------------------------------

    roadmap = GeneratedRoadmap.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    roadmap_progress = 0
    completed_phases = 0
    total_phases = 0
    current_phase = None
    latest_roadmap_attempt = None

    if roadmap:

        phases = roadmap.roadmap_data.get("phases", [])

        total_phases = len(phases)

        assessments = RoadmapAssessment.objects.filter(
            roadmap=roadmap
        ).order_by("phase_number")

        completed_phase_numbers = set(
            assessments.filter(
                is_completed=True
            ).values_list(
                "phase_number",
                flat=True
            )
        )

        completed_phases = len(
            completed_phase_numbers
        )

        if total_phases > 0:
            roadmap_progress = round(
                (completed_phases / total_phases) * 100
            )

        # -----------------------------------
        # Find current phase
        # -----------------------------------

        for index, phase in enumerate(phases):

            phase_number = phase.get(
                "phase",
                index + 1
            )

            if phase_number not in completed_phase_numbers:

                current_phase = phase
                break

        # -----------------------------------
        # If every phase is completed
        # -----------------------------------

        if current_phase is None and phases:

            current_phase = phases[-1]

        # -----------------------------------
        # Latest roadmap assessment attempt
        # -----------------------------------

        latest_roadmap_attempt = (
            RoadmapAssessmentAttempt.objects
            .filter(
                user=request.user,
                assessment__roadmap=roadmap
            )
            .select_related("assessment")
            .order_by("-completed_at")
            .first()
        )
       # =========================================================
        # JOURNEY STATUS
        # =========================================================

        profile_completed = bool(
            request.user.first_name.strip()
            and request.user.email.strip()
        )

        assessment_completed = assessment_result is not None

        ai_analysis_completed = bool(
            assessment_result
            and career_goal
        )

        roadmap_generated = roadmap is not None    
        # -----------------------------------
        # Dashboard
        # -----------------------------------

        return render(
            request,
            "dashboard/dashboard.html",
            {
                "career_goal": career_goal,
                "assessment_result": assessment_result,
                "skill_gaps": skill_gaps,
                "priority_skill": priority_skill,

                # Roadmap
                "roadmap": roadmap,
                "roadmap_progress": roadmap_progress,
                "completed_phases": completed_phases,
                "total_phases": total_phases,
                "current_phase": current_phase,
                "latest_roadmap_attempt": latest_roadmap_attempt,

                # Journey
                "profile_completed": profile_completed,
                "assessment_completed": assessment_completed,
                "ai_analysis_completed": ai_analysis_completed,
                "roadmap_generated": roadmap_generated,
            }
        )

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

    # -----------------------------------
    # AI Roadmap Progress
    # -----------------------------------

    roadmap = GeneratedRoadmap.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    roadmap_progress = 0
    completed_phases = 0
    total_phases = 0
    current_phase = None
    latest_roadmap_attempt = None

    if roadmap:

        phases = roadmap.roadmap_data.get("phases", [])

        total_phases = len(phases)

        assessments = RoadmapAssessment.objects.filter(
            roadmap=roadmap
        ).order_by("phase_number")

        completed_phase_numbers = set(
            assessments.filter(
                is_completed=True
            ).values_list(
                "phase_number",
                flat=True
            )
        )

        completed_phases = len(
            completed_phase_numbers
        )

        if total_phases > 0:
            roadmap_progress = round(
                (completed_phases / total_phases) * 100
            )

        # -----------------------------------
        # Find current phase
        # -----------------------------------

        for index, phase in enumerate(phases):

            phase_number = phase.get(
                "phase",
                index + 1
            )

            if phase_number not in completed_phase_numbers:

                current_phase = phase
                break

        # -----------------------------------
        # If every phase is completed
        # -----------------------------------

        if current_phase is None and phases:

            current_phase = phases[-1]

        # -----------------------------------
        # Latest roadmap assessment attempt
        # -----------------------------------

        latest_roadmap_attempt = (
            RoadmapAssessmentAttempt.objects
            .filter(
                user=request.user,
                assessment__roadmap=roadmap
            )
            .select_related("assessment")
            .order_by("-completed_at")
            .first()
        )

@login_required
def admin_reports(request):

    # =========================================================
    # 1. STUDENTS
    # =========================================================

    students = User.objects.filter(
        is_staff=False
    ).order_by("first_name", "last_name")

    total_students = students.count()

    # =========================================================
    # 2. ASSESSMENT / ROADMAP OVERVIEW
    # =========================================================

    assessed_students = AssessmentResult.objects.filter(
        user__in=students
    ).values("user").distinct().count()

    roadmaps = GeneratedRoadmap.objects.filter(
        user__in=students,
        is_active=True
    )

    total_roadmaps = roadmaps.count()

    completed_roadmaps = 0
    students_in_progress = 0
    total_progress = 0

    # =========================================================
    # 3. STUDENT PROGRESS REPORT
    # =========================================================

    student_progress = []

    for student in students:

        # -----------------------------------------
        # Assessment
        # -----------------------------------------

        assessment = SkillAssessment.objects.filter(
            user=student
        ).select_related(
            "career_path"
        ).first()

        assessment_result = AssessmentResult.objects.filter(
            user=student
        ).order_by(
            "-completed_at"
        ).first()

        # -----------------------------------------
        # Career
        # -----------------------------------------

        career_name = "Not Selected"

        if assessment and assessment.career_path:
            career_name = assessment.career_path.name

        # -----------------------------------------
        # Assessment percentage
        # -----------------------------------------

        assessment_percentage = None

        if assessment_result:
            assessment_percentage = round(
                assessment_result.percentage,
                1
            )

        # -----------------------------------------
        # Roadmap
        # -----------------------------------------

        roadmap = GeneratedRoadmap.objects.filter(
            user=student,
            is_active=True
        ).first()

        roadmap_percentage = 0
        current_phase = "Not Started"
        roadmap_status = "Not Generated"

        if roadmap:

            phases = roadmap.roadmap_data.get(
                "phases",
                []
            )

            total_phases = len(phases)

            completed_phases = RoadmapAssessment.objects.filter(
                roadmap=roadmap,
                is_completed=True
            ).values(
                "phase_number"
            ).distinct().count()

            # Calculate roadmap progress

            if total_phases > 0:

                roadmap_percentage = round(
                    (
                        completed_phases
                        / total_phases
                    ) * 100
                )

            roadmap_status = "In Progress"

            if roadmap_percentage == 100:
                roadmap_status = "Completed"

            # Find current phase

            for index, phase in enumerate(phases):

                phase_number = phase.get(
                    "phase",
                    index + 1
                )

                phase_completed = RoadmapAssessment.objects.filter(
                    roadmap=roadmap,
                    phase_number=phase_number,
                    is_completed=True
                ).exists()

                if not phase_completed:

                    current_phase = phase.get(
                        "title",
                        f"Phase {phase_number}"
                    )

                    break

            # If all phases are completed

            if roadmap_percentage == 100 and phases:

                current_phase = phases[-1].get(
                    "title",
                    "Completed"
                )

            # Overview calculations

            total_progress += roadmap_percentage

            if roadmap_percentage == 100:

                completed_roadmaps += 1

            elif roadmap_percentage > 0:

                students_in_progress += 1

        # -----------------------------------------
        # Student status
        # -----------------------------------------

        if not assessment_result:

            student_status = "Assessment Pending"

        elif not roadmap:

            student_status = "Roadmap Pending"

        elif roadmap_percentage == 100:

            student_status = "Completed"

        elif roadmap_percentage > 0:

            student_status = "In Progress"

        else:

            student_status = "Started"

        student_progress.append({

            "student": student,

            "career": career_name,

            "assessment": assessment_percentage,

            "roadmap_progress": roadmap_percentage,

            "current_phase": current_phase,

            "status": student_status,

        })

    # =========================================================
    # 4. AVERAGE ROADMAP PROGRESS
    # =========================================================

    average_progress = 0

    if total_roadmaps > 0:

        total_roadmap_progress = sum(
            item["roadmap_progress"]
            for item in student_progress
            if item["roadmap_progress"] is not None
        )

        average_progress = round(
            total_roadmap_progress
            / total_roadmaps
        )

    # =========================================================
    # 5. STUDENTS REQUIRING ATTENTION
    # =========================================================

    attention_students = []

    for item in student_progress:

        reasons = []

        # Assessment pending

        if item["assessment"] is None:

            reasons.append(
                "Assessment not completed"
            )

        # Low assessment

        elif item["assessment"] < 50:

            reasons.append(
                "Low assessment score"
            )

        # Roadmap not started

        if item["assessment"] is not None:

            if item["roadmap_progress"] == 0:

                reasons.append(
                    "Roadmap not started"
                )

            elif item["roadmap_progress"] < 50:

                reasons.append(
                    "Low roadmap progress"
                )

        if reasons:

            attention_students.append({

                "student": item["student"],

                "career": item["career"],

                "assessment": item["assessment"],

                "progress": item["roadmap_progress"],

                "reasons": reasons,

            })

    # =========================================================
    # 6. CONTEXT
    # =========================================================

    context = {

        # Overview

        "total_students": total_students,

        "assessed_students": assessed_students,

        "total_roadmaps": total_roadmaps,

        "students_in_progress": students_in_progress,

        "completed_roadmaps": completed_roadmaps,

        "average_progress": average_progress,

        # Student Progress

        "student_progress": student_progress,

        # Attention

        "attention_students": attention_students,

    }

    return render(
        request,
        "dashboard/admin_reports.html",
        context
    )