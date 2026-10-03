from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .services import generate_ai_roadmap
from .models import GeneratedRoadmap

from roadmap.models import (
    RoadmapTopicProgress,
    RoadmapAssessment,
)

@login_required
def generate_roadmap(request):

    try:

        # Generate roadmap using Gemini AI
        roadmap = generate_ai_roadmap(
            request.user
        )

        # Deactivate previous roadmap
        GeneratedRoadmap.objects.filter(
            user=request.user,
            is_active=True
        ).update(
            is_active=False
        )

        # Save new AI-generated roadmap
        generated = GeneratedRoadmap.objects.create(

            user=request.user,

            career=roadmap["career"],

            roadmap_data=roadmap,

            is_active=True
        )
        create_roadmap_progress(
            request.user,
            generated
        )

        return JsonResponse({

            "success": True,

            "message": "AI roadmap generated successfully.",

            "roadmap_id": generated.id,

            "roadmap": roadmap

        })

    except Exception as e:

        return JsonResponse({

            "success": False,

            "message": str(e)

        }, status=500)
    
def create_roadmap_progress(user, roadmap):

    RoadmapTopicProgress.objects.filter(
        user=user,
        roadmap=roadmap
    ).delete()

    phases = roadmap.roadmap_data.get(
        "phases",
        []
    )

    progress_objects = []

    for phase in phases:

        phase_number = phase.get(
            "phase",
            1
        )

        topics = phase.get(
            "topics",
            []
        )

        for topic in topics:

            progress_objects.append(
                RoadmapTopicProgress(
                    user=user,
                    roadmap=roadmap,
                    phase_number=phase_number,
                    topic=topic,
                    status="not_started"
                )
            )

    RoadmapTopicProgress.objects.bulk_create(
        progress_objects
    )

@login_required
def generate_roadmap_page(request):

    # Check whether the student already has a saved roadmap
    existing_roadmap = GeneratedRoadmap.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    try:

        roadmap = generate_ai_roadmap(request.user)

        # Deactivate previous roadmap
        GeneratedRoadmap.objects.filter(
            user=request.user,
            is_active=True
        ).update(
            is_active=False
        )

        # Save new AI roadmap
        generated_roadmap = GeneratedRoadmap.objects.create(
            user=request.user,
            career=roadmap["career"],
            roadmap_data=roadmap,
            is_active=True
        )

        create_roadmap_progress(
            request.user,
            generated_roadmap
        )
        return redirect("my_roadmap")

    except Exception as e:

        # If a roadmap already exists, show it instead of
        # displaying an error page.
        if existing_roadmap:

            return render(
                request,
                "roadmap/my_roadmap.html",
                {
                    "roadmap": existing_roadmap,
                    "ai_error": str(e)
                }
            )

        return render(
            request,
            "roadmap/my_roadmap.html",
            {
                "roadmap": None,
                "ai_error": str(e)
            }
        )

@login_required
def my_roadmap(request):

    roadmap = GeneratedRoadmap.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if not roadmap:
        return redirect("generate_roadmap_page")

    # --------------------------------------------------
    # Get AI-generated phases
    # --------------------------------------------------

    phases = roadmap.roadmap_data.get(
        "phases",
        []
    )

    # --------------------------------------------------
    # Get roadmap assessments
    # --------------------------------------------------

    assessments = RoadmapAssessment.objects.filter(
        roadmap=roadmap
    ).order_by(
        "phase_number"
    )

    assessment_map = {
        assessment.phase_number: assessment
        for assessment in assessments
    }

    # --------------------------------------------------
    # Build phase information
    # --------------------------------------------------

    roadmap_phases = []

    for index, phase in enumerate(phases):

        phase_number = phase.get(
            "phase",
            index + 1
        )

        assessment = assessment_map.get(
            phase_number
        )

        # ----------------------------------------------
        # Phase 1 is always available
        # ----------------------------------------------

        if phase_number == 1:

            is_unlocked = True

        else:

            previous_assessment = assessment_map.get(
                phase_number - 1
            )

            is_unlocked = (
                previous_assessment is not None
                and previous_assessment.is_completed
            )

        # ----------------------------------------------
        # Determine status
        # ----------------------------------------------

        if assessment and assessment.is_completed:

            status = "completed"

        elif is_unlocked:

            status = "available"

        else:

            status = "locked"

        # ----------------------------------------------
        # Add information to phase
        # ----------------------------------------------

        roadmap_phases.append({

            "phase": phase,

            "phase_number": phase_number,

            "assessment": assessment,

            "status": status,

            "is_unlocked": is_unlocked,

        })

    # --------------------------------------------------
    # Overall phase progress
    # --------------------------------------------------

    total_phases = len(
        roadmap_phases
    )

    completed_phases = sum(
        1
        for item in roadmap_phases
        if item["status"] == "completed"
    )

    if total_phases > 0:

        progress_percentage = round(
            (
                completed_phases
                / total_phases
            ) * 100
        )

    else:

        progress_percentage = 0

    # --------------------------------------------------
    # Render roadmap
    # --------------------------------------------------

    return render(
        request,
        "roadmap/my_roadmap.html",
        {

            "roadmap": roadmap,

            "roadmap_phases": roadmap_phases,

            "total_phases": total_phases,

            "completed_phases": completed_phases,

            "progress_percentage": progress_percentage,

        }
    )