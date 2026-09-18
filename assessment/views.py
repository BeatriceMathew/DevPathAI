from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import (AssessmentQuestion,AssessmentResult,AssessmentAnswer,SkillAssessment,)

def admin_check(user):
    return user.is_authenticated and user.is_staff
# ============================================================
# STUDENT ASSESSMENT
# ============================================================
@login_required
def assessment(request):
    from accounts.models import CareerPath
    from .models import (
        AssessmentQuestion,
        AssessmentResult,
        AssessmentAnswer,
        SkillAssessment,
        SkillAssessmentResult,
    )

    career_paths = CareerPath.objects.filter(
        is_active=True
    ).order_by("name")

    selected_career_id = request.GET.get("career")

    selected_career = None
    questions = AssessmentQuestion.objects.none()

    # ================= GET =================

    if selected_career_id:
        try:
            selected_career = CareerPath.objects.get(
                id=selected_career_id,
                is_active=True
            )

            questions = AssessmentQuestion.objects.filter(
                career_paths=selected_career
            ).select_related("skill").distinct().order_by("id")

        except CareerPath.DoesNotExist:
            selected_career = None

    # ================= POST =================

    if request.method == "POST":

        career_id = request.POST.get("career_path")

        if not career_id:
            messages.error(
                request,
                "Please select a career path."
            )
            return redirect("assessment")

        try:
            selected_career = CareerPath.objects.get(
                id=career_id,
                is_active=True
            )

        except CareerPath.DoesNotExist:
            messages.error(
                request,
                "Invalid career path selected."
            )
            return redirect("assessment")

        # Get career-specific questions
        questions = AssessmentQuestion.objects.filter(
            career_paths=selected_career
        ).select_related("skill").distinct().order_by("id")

        # ================= OVERALL SCORE =================

        score = 0
        total_questions = questions.count()

        # ================= SAVE CAREER =================

        assessment_obj, created = SkillAssessment.objects.get_or_create(
            user=request.user
        )

        assessment_obj.career_path = selected_career
        assessment_obj.career_goal = selected_career.name
        assessment_obj.save()

        # ================= RESULT =================

        for question in questions:

            selected_answer = request.POST.get(
                f"question_{question.id}",
                ""
            )

            if selected_answer == question.correct_answer:
                score += 1

        percentage = (
            (score / total_questions) * 100
            if total_questions > 0
            else 0
        )

        result, created = AssessmentResult.objects.update_or_create(
            user=request.user,
            defaults={
                "score": score,
                "total_questions": total_questions,
                "percentage": percentage,
            }
        )

        # ================= REMOVE OLD DATA =================

        result.answers.all().delete()
        result.skill_results.all().delete()

        # ================= SAVE ANSWERS =================

        for question in questions:

            selected_answer = request.POST.get(
                f"question_{question.id}",
                ""
            )

            AssessmentAnswer.objects.create(
                result=result,
                question=question,
                selected_answer=selected_answer,
                is_correct=(
                    selected_answer == question.correct_answer
                )
            )

        # ==================================================
        # SKILL-WISE ANALYSIS
        # ==================================================

        skill_data = {}

        for question in questions:

            # Ignore questions without a skill
            if not question.skill:
                continue

            skill_id = question.skill.id

            if skill_id not in skill_data:
                skill_data[skill_id] = {
                    "skill": question.skill,
                    "total": 0,
                    "correct": 0,
                }

            skill_data[skill_id]["total"] += 1

            selected_answer = request.POST.get(
                f"question_{question.id}",
                ""
            )

            if selected_answer == question.correct_answer:
                skill_data[skill_id]["correct"] += 1

        # ==================================================
        # CREATE SKILL RESULTS
        # ==================================================

        for data in skill_data.values():

            skill = data["skill"]
            total = data["total"]
            correct = data["correct"]

            skill_percentage = (
                (correct / total) * 100
                if total > 0
                else 0
            )

            # Determine skill level
            if skill_percentage < 40:
                level = "Beginner"

            elif skill_percentage < 60:
                level = "Intermediate"

            elif skill_percentage < 80:
                level = "Advanced"

            else:
                level = "Expert"

            SkillAssessmentResult.objects.create(
                result=result,
                skill=skill,
                correct_answers=correct,
                total_questions=total,
                percentage=skill_percentage,
                level=level,
            )

        return redirect("assessment_result")

    # ================= RENDER =================

    return render(
        request,
        "assessment/assessment.html",
        {
            "career_paths": career_paths,
            "selected_career": selected_career,
            "questions": questions,
        }
    )

# ============================================================
# ADMIN - QUESTION BANK
# ============================================================
@login_required
@user_passes_test(admin_check)
def admin_assessment_questions(request):
    questions = AssessmentQuestion.objects.all().order_by("id")

    programming_count = AssessmentQuestion.objects.filter(
        category="programming"
    ).count()

    frameworks_count = AssessmentQuestion.objects.filter(
        category="frameworks"
    ).count()

    databases_count = AssessmentQuestion.objects.filter(
        category="databases"
    ).count()

    tools_count = AssessmentQuestion.objects.filter(
        category="tools"
    ).count()

    context = {
        "questions": questions,

        "total_questions": questions.count(),

        "programming_count": programming_count,
        "frameworks_count": frameworks_count,
        "databases_count": databases_count,
        "tools_count": tools_count,
    }

    return render(
        request,
        "assessment/admin_assessment_questions.html",
        context
    )
# ============================================================
# ADMIN - ADD QUESTION
# ============================================================

@login_required
@user_passes_test(admin_check)
def add_assessment_question(request):
    from accounts.models import Skill, CareerPath

    skills = Skill.objects.filter(is_active=True).order_by("name")
    career_paths = CareerPath.objects.filter(is_active=True).order_by("name")

    if request.method == "POST":
        question = request.POST.get("question", "").strip()
        option_a = request.POST.get("option_a", "").strip()
        option_b = request.POST.get("option_b", "").strip()
        option_c = request.POST.get("option_c", "").strip()
        option_d = request.POST.get("option_d", "").strip()
        correct_answer = request.POST.get("correct_answer", "")
        category = request.POST.get("category", "")
        difficulty = request.POST.get("difficulty", "")
        skill_id = request.POST.get("skill", "")
        career_path_ids = request.POST.getlist("career_paths")

        if not question:
            return render(request, "assessment/add_assessment_question.html", {
                "error": "Question is required.",
                "data": request.POST,
                "skills": skills,
                "career_paths": career_paths,
            })

        if not all([option_a, option_b, option_c, option_d]):
            return render(request, "assessment/add_assessment_question.html", {
                "error": "All four options are required.",
                "data": request.POST,
                "skills": skills,
                "career_paths": career_paths,
            })

        if correct_answer not in ["A", "B", "C", "D"]:
            return render(request, "assessment/add_assessment_question.html", {
                "error": "Please select the correct answer.",
                "data": request.POST,
                "skills": skills,
                "career_paths": career_paths,
            })

        if category not in ["programming", "frameworks", "databases", "tools"]:
            return render(request, "assessment/add_assessment_question.html", {
                "error": "Please select a valid category.",
                "data": request.POST,
                "skills": skills,
                "career_paths": career_paths,
            })

        if difficulty not in ["easy", "medium", "hard"]:
            return render(request, "assessment/add_assessment_question.html", {
                "error": "Please select a valid difficulty level.",
                "data": request.POST,
                "skills": skills,
                "career_paths": career_paths,
            })

        question_obj = AssessmentQuestion.objects.create(
            question=question,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            category=category,
            difficulty=difficulty,
            skill_id=skill_id if skill_id else None,
        )

        if career_path_ids:
            question_obj.career_paths.set(career_path_ids)

        messages.success(
            request,
            "Assessment question added successfully."
        )

        return redirect("admin_assessment_questions")

    return render(
        request,
        "assessment/add_assessment_question.html",
        {
            "skills": skills,
            "career_paths": career_paths,
        }
    )


# ============================================================
# ADMIN - EDIT QUESTION
# ============================================================
@login_required
@user_passes_test(admin_check)
def edit_assessment_question(request, question_id):
    from accounts.models import Skill, CareerPath

    question_obj = AssessmentQuestion.objects.get(id=question_id)

    skills = Skill.objects.filter(is_active=True).order_by("name")
    career_paths = CareerPath.objects.filter(is_active=True).order_by("name")

    if request.method == "POST":
        question = request.POST.get("question", "").strip()
        option_a = request.POST.get("option_a", "").strip()
        option_b = request.POST.get("option_b", "").strip()
        option_c = request.POST.get("option_c", "").strip()
        option_d = request.POST.get("option_d", "").strip()

        correct_answer = request.POST.get("correct_answer", "")
        category = request.POST.get("category", "")
        difficulty = request.POST.get("difficulty", "").strip()

        skill_id = request.POST.get("skill", "")
        career_path_ids = request.POST.getlist("career_paths")

        if not question:
            return render(
                request,
                "assessment/edit_assessment_question.html",
                {
                    "question": question_obj,
                    "error": "Question is required.",
                    "skills": skills,
                    "career_paths": career_paths,
                }
            )

        if not all([option_a, option_b, option_c, option_d]):
            return render(
                request,
                "assessment/edit_assessment_question.html",
                {
                    "question": question_obj,
                    "error": "All four options are required.",
                    "skills": skills,
                    "career_paths": career_paths,
                }
            )

        if correct_answer not in ["A", "B", "C", "D"]:
            return render(
                request,
                "assessment/edit_assessment_question.html",
                {
                    "question": question_obj,
                    "error": "Please select a valid correct answer.",
                    "skills": skills,
                    "career_paths": career_paths,
                }
            )

        if category not in [
            "programming",
            "frameworks",
            "databases",
            "tools"
        ]:
            return render(
                request,
                "assessment/edit_assessment_question.html",
                {
                    "question": question_obj,
                    "error": "Please select a valid category.",
                    "skills": skills,
                    "career_paths": career_paths,
                }
            )

        if difficulty not in ["easy", "medium", "hard"]:
            return render(
                request,
                "assessment/edit_assessment_question.html",
                {
                    "question": question_obj,
                    "error": "Please select a valid difficulty level.",
                    "skills": skills,
                    "career_paths": career_paths,
                }
            )

        # Update question
        question_obj.question = question
        question_obj.option_a = option_a
        question_obj.option_b = option_b
        question_obj.option_c = option_c
        question_obj.option_d = option_d
        question_obj.correct_answer = correct_answer
        question_obj.category = category
        question_obj.difficulty = difficulty

        # Update skill
        question_obj.skill_id = skill_id if skill_id else None

        question_obj.save()

        # Update career paths
        question_obj.career_paths.set(career_path_ids)

        messages.success(
            request,
            "Assessment question updated successfully."
        )

        return redirect("admin_assessment_questions")

    return render(
        request,
        "assessment/edit_assessment_question.html",
        {
            "question": question_obj,
            "skills": skills,
            "career_paths": career_paths,
        }
    )

# ============================================================
# ADMIN - DELETE QUESTION
# ============================================================

@login_required
@user_passes_test(admin_check)
def delete_assessment_question(request, question_id):

    question_obj = AssessmentQuestion.objects.get(
        id=question_id
    )

    if request.method == "POST":

        question_obj.delete()

        messages.success(
            request,
            "Assessment question deleted successfully."
        )

        return redirect(
            "admin_assessment_questions"
        )


    return render(
        request,
        "assessment/delete_assessment_question.html",
        {
            "question": question_obj
        }
    )

@login_required
def assessment_result(request):
    try:
        result = AssessmentResult.objects.get(user=request.user)
    except AssessmentResult.DoesNotExist:
        return redirect("assessment")

    return render(
        request,
        "assessment/assessment_result.html",
        {
            "result": result,
        }
    )