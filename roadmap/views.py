from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone

from .models import (
    RoadmapTopicProgress,
    RoadmapAssessment,
    RoadmapAssessmentAttempt,
)

from ai_engine.models import GeneratedRoadmap
from ai_engine.services import generate_phase_assessment


# ============================================================
# START TOPIC
# ============================================================

@login_required
def start_topic(request, progress_id):

    progress = get_object_or_404(
        RoadmapTopicProgress,
        id=progress_id,
        user=request.user
    )

    progress.status = "in_progress"
    progress.save()

    return redirect("my_roadmap")


# ============================================================
# COMPLETE TOPIC
# ============================================================

@login_required
def complete_topic(request, progress_id):

    progress = get_object_or_404(
        RoadmapTopicProgress,
        id=progress_id,
        user=request.user
    )

    progress.status = "completed"
    progress.completed_at = timezone.now()
    progress.save()

    return redirect("my_roadmap")


# ============================================================
# START / TAKE ROADMAP ASSESSMENT
# ============================================================

@login_required
def start_roadmap_assessment(request, phase_number):

    # --------------------------------------------------------
    # 1. Get student's active roadmap
    # --------------------------------------------------------

    roadmap = GeneratedRoadmap.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if not roadmap:
        return redirect("generate_roadmap_page")

    # --------------------------------------------------------
    # 2. Get roadmap phases
    # --------------------------------------------------------

    phases = roadmap.roadmap_data.get("phases", [])

    phase = None

    for item in phases:

        if item.get("phase") == phase_number:
            phase = item
            break

    if not phase:
        return redirect("my_roadmap")

    # --------------------------------------------------------
    # 3. Check previous phase
    # --------------------------------------------------------

    if phase_number > 1:

        previous_assessment = RoadmapAssessment.objects.filter(
            roadmap=roadmap,
            phase_number=phase_number - 1
        ).first()

        # Previous assessment must exist
        if not previous_assessment:
            return redirect("my_roadmap")

        # Previous assessment must be passed
        if not previous_assessment.is_completed:
            return redirect("my_roadmap")

    # --------------------------------------------------------
    # 4. Get existing assessment
    # --------------------------------------------------------

    assessment = RoadmapAssessment.objects.filter(
        roadmap=roadmap,
        phase_number=phase_number
    ).first()

    # --------------------------------------------------------
    # 5. Generate AI assessment if it doesn't exist
    # --------------------------------------------------------

    if not assessment:

        try:

            ai_assessment = generate_phase_assessment(
                user=request.user,
                roadmap=roadmap,
                phase_number=phase_number
            )

        except Exception as e:

            return render(
                request,
                "roadmap/assessment_error.html",
                {
                    "error": str(e),
                    "phase": phase
                }
            )

        assessment = RoadmapAssessment.objects.create(

            roadmap=roadmap,

            phase_number=phase_number,

            phase_title=ai_assessment.get(
                "phase_title",
                phase.get("title", "")
            ),

            questions=ai_assessment.get(
                "questions",
                []
            ),

            passing_percentage=70,

            is_unlocked=True,

            is_completed=False,

            best_score=0
        )

    # ========================================================
    # 6. PROCESS ASSESSMENT SUBMISSION
    # ========================================================

    if request.method == "POST":

        questions = assessment.questions

        score = 0

        answers = []

        # ----------------------------------------------------
        # Check every question
        # ----------------------------------------------------

        for index, question in enumerate(questions):

            selected_answer = request.POST.get(
                f"question_{index}",
                ""
            )

            correct_answer = question.get(
                "correct_answer",
                ""
            )

            is_correct = (
                selected_answer.upper()
                == correct_answer.upper()
            )

            if is_correct:
                score += 1

            answers.append({
                "question": question.get(
                    "question",
                    ""
                ),

                "selected_answer": selected_answer,

                "correct_answer": correct_answer,

                "is_correct": is_correct,

                "topic": question.get(
                    "topic",
                    ""
                )
            })

        # ----------------------------------------------------
        # Calculate percentage
        # ----------------------------------------------------

        total_questions = len(questions)

        percentage = 0

        if total_questions > 0:

            percentage = round(
                (score / total_questions) * 100,
                2
            )

        # ----------------------------------------------------
        # Check pass/fail
        # ----------------------------------------------------

        passed = (
            percentage >= assessment.passing_percentage
        )

        # ----------------------------------------------------
        # Save assessment attempt
        # ----------------------------------------------------

        attempt = RoadmapAssessmentAttempt.objects.create(

            assessment=assessment,

            user=request.user,

            score=score,

            total_questions=total_questions,

            percentage=percentage,

            passed=passed,

            answers=answers
        )

        # ----------------------------------------------------
        # Update best score
        # ----------------------------------------------------

        if percentage > assessment.best_score:

            assessment.best_score = percentage

        # ----------------------------------------------------
        # If passed
        # ----------------------------------------------------

        if passed:

            assessment.is_completed = True
            assessment.is_unlocked = True

            # -----------------------------------------------
            # Unlock next assessment if it already exists
            # -----------------------------------------------

            next_assessment = RoadmapAssessment.objects.filter(
                roadmap=roadmap,
                phase_number=phase_number + 1
            ).first()

            if next_assessment:

                next_assessment.is_unlocked = True

                next_assessment.save(
                    update_fields=["is_unlocked"]
                )

        assessment.save()

        # ----------------------------------------------------
        # Redirect to result page
        # ----------------------------------------------------

        return redirect(
            "roadmap:roadmap_assessment_result",
            attempt_id=attempt.id
        )

    # ========================================================
    # 7. If assessment is already completed
    # ========================================================

    if assessment.is_completed:

        latest_attempt = assessment.attempts.filter(
            user=request.user
        ).first()

        if latest_attempt:

            return redirect(
                "roadmap:roadmap_assessment_result",
                attempt_id=latest_attempt.id
            )

    # ========================================================
    # 8. Show assessment page
    # ========================================================

    return render(
        request,
        "roadmap/roadmap_assessment.html",
        {
            "assessment": assessment,
            "phase": phase
        }
    )


# ============================================================
# ASSESSMENT RESULT
# ============================================================

@login_required
def roadmap_assessment_result(request, attempt_id):

    attempt = get_object_or_404(
        RoadmapAssessmentAttempt,
        id=attempt_id,
        user=request.user
    )

    assessment = attempt.assessment
    roadmap = assessment.roadmap

    phases = roadmap.roadmap_data.get("phases", [])

    next_phase = None

    # Find the next phase after the current assessment
    for phase in phases:

        phase_number = phase.get("phase")

        if phase_number == assessment.phase_number + 1:
            next_phase = phase_number
            break

    return render(
        request,
        "roadmap/roadmap_assessment_result.html",
        {
            "attempt": attempt,
            "assessment": assessment,
            "roadmap": roadmap,
            "next_phase": next_phase,
        }
    )

@login_required
def my_progress(request):
    roadmap = GeneratedRoadmap.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if not roadmap:
        return redirect("generate_roadmap_page")

    phases = roadmap.roadmap_data.get("phases", [])

    assessments = RoadmapAssessment.objects.filter(
        roadmap=roadmap
    ).order_by("phase_number")

    attempts = RoadmapAssessmentAttempt.objects.filter(
        user=request.user,
        assessment__roadmap=roadmap
    ).select_related("assessment").order_by(
        "assessment__phase_number",
        "-completed_at"
    )

    # Keep only the latest attempt for each phase
    latest_attempts = {}

    for attempt in attempts:
        phase_number = attempt.assessment.phase_number

        if phase_number not in latest_attempts:
            latest_attempts[phase_number] = attempt

    phase_progress = []

    completed_phases = 0
    current_phase = None

    for index, phase in enumerate(phases):

        phase_number = phase.get("phase", index + 1)

        assessment = assessments.filter(
            phase_number=phase_number
        ).first()

        latest_attempt = latest_attempts.get(
            phase_number
        )

        # --------------------------------------------------
        # Phase status
        # --------------------------------------------------

        if assessment and assessment.is_completed:

            status = "completed"
            progress = 100
            completed_phases += 1

        elif phase_number == 1:

            status = "available"
            progress = 0

            if current_phase is None:
                current_phase = phase_number

        else:

            previous_assessment = assessments.filter(
                phase_number=phase_number - 1
            ).first()

            if (
                previous_assessment
                and previous_assessment.is_completed
            ):
                status = "available"
                progress = 0

                if current_phase is None:
                    current_phase = phase_number

            else:
                status = "locked"
                progress = 0

        phase_progress.append({
            "phase": phase,
            "phase_number": phase_number,
            "assessment": assessment,
            "latest_attempt": latest_attempt,
            "status": status,
            "progress": progress,
        })

    # ------------------------------------------------------
    # Overall progress
    # ------------------------------------------------------

    total_phases = len(phases)

    overall_progress = (
        round((completed_phases / total_phases) * 100)
        if total_phases > 0
        else 0
    )

    # ------------------------------------------------------
    # Assessment statistics
    # ------------------------------------------------------

    total_assessments = len(latest_attempts)

    passed_assessments = sum(
        1
        for attempt in latest_attempts.values()
        if attempt.passed
    )

    # ------------------------------------------------------
    # Current phase
    # ------------------------------------------------------

    current_phase_data = None

    if current_phase:

        for item in phase_progress:

            if item["phase_number"] == current_phase:
                current_phase_data = item
                break

    return render(
        request,
        "roadmap/my_progress.html",
        {
            "roadmap": roadmap,
            "phase_progress": phase_progress,
            "total_phases": total_phases,
            "completed_phases": completed_phases,
            "overall_progress": overall_progress,
            "total_assessments": total_assessments,
            "passed_assessments": passed_assessments,
            "current_phase": current_phase_data,
        }
    )
# Create your views here.
