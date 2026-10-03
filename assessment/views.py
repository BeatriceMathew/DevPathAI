from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
import random
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

    # -------------------------------------------------
    # SETTINGS
    # -------------------------------------------------

    DIFFICULTY_LIMITS = {
        "easy": 6,
        "medium": 20,
        "hard": 24,
    }

    TOTAL_REQUIRED = 50

    # -------------------------------------------------
    # CAREER PATHS
    # -------------------------------------------------

    career_paths = CareerPath.objects.filter(
        is_active=True
    ).order_by("name")

    selected_career_id = request.GET.get("career")
    selected_career = None
    questions = AssessmentQuestion.objects.none()

    # -------------------------------------------------
    # GET - STUDENT SELECTS CAREER
    # -------------------------------------------------

    if selected_career_id:
        try:
            selected_career = CareerPath.objects.get(
                id=selected_career_id,
                is_active=True
            )

        except CareerPath.DoesNotExist:
            selected_career = None

        if selected_career:

            # Get all questions for selected career
            available_questions = list(
                AssessmentQuestion.objects.filter(
                    career_paths=selected_career,
                    skill__isnull=False
                )
                .select_related("skill")
                .distinct()
            )

            # Check total questions
            if len(available_questions) < TOTAL_REQUIRED:
                messages.error(
                    request,
                    f"This career path does not have enough questions. "
                    f"At least {TOTAL_REQUIRED} questions are required."
                )

                questions = AssessmentQuestion.objects.none()

            else:

                    # -------------------------------------------------
                # SELECT QUESTIONS BY EXACT SKILL + DIFFICULTY
                # -------------------------------------------------
    
                QUESTION_DISTRIBUTION = {
                    "Python": {"easy": 1, "medium": 4, "hard": 5},
                    "Django": {"easy": 1, "medium": 4, "hard": 4},
                    "FastAPI": {"easy": 1, "medium": 3, "hard": 3},
                    "SQL / Database": {"easy": 1, "medium": 3, "hard": 4},
                    "REST API": {"easy": 1, "medium": 3, "hard": 4},
                    "Git & GitHub": {"easy": 1, "medium": 3, "hard": 4},
                }
    
                selected_questions = []
                distribution_error = False
    
                if selected_career.name == "Python Developer":
                    for skill_name, difficulty_counts in QUESTION_DISTRIBUTION.items():
                        for difficulty, required_count in difficulty_counts.items():
                            matching_questions = [
                                q for q in available_questions
                                if q.skill.name == skill_name
                                and q.difficulty == difficulty
                            ]
    
                            if len(matching_questions) < required_count:
                                messages.error(
                                    request,
                                    f"Not enough {difficulty.title()} questions "
                                    f"for {skill_name}. Required: {required_count}, "
                                    f"Available: {len(matching_questions)}."
                                )
                                distribution_error = True
                                break
    
                            random.shuffle(matching_questions)
                            selected_questions.extend(
                                matching_questions[:required_count]
                            )
    
                        if distribution_error:
                            break
    
                    if distribution_error:
                        selected_questions = []
    
                else:
                    # Fallback for other career paths until they receive
                    # their own exact skill-wise distributions.
                    difficulty_questions = {
                        "easy": {},
                        "medium": {},
                        "hard": {},
                    }
    
                    for question in available_questions:
                        difficulty = question.difficulty
                        skill_id = question.skill.id
    
                        if difficulty not in difficulty_questions:
                            continue
    
                        if skill_id not in difficulty_questions[difficulty]:
                            difficulty_questions[difficulty][skill_id] = []
    
                        difficulty_questions[difficulty][skill_id].append(question)
    
                    for difficulty, required_count in DIFFICULTY_LIMITS.items():
                        skill_groups = difficulty_questions[difficulty]
                        available_count = sum(
                            len(group) for group in skill_groups.values()
                        )
    
                        if available_count < required_count:
                            messages.error(
                                request,
                                f"Not enough {difficulty.title()} questions "
                                f"for {selected_career.name}. "
                                f"Required: {required_count}, "
                                f"Available: {available_count}."
                            )
                            selected_questions = []
                            break
    
                        for group in skill_groups.values():
                            random.shuffle(group)
    
                        skill_ids = list(skill_groups.keys())
                        random.shuffle(skill_ids)
                        selected_for_difficulty = []
    
                        while len(selected_for_difficulty) < required_count:
                            added_question = False
    
                            for skill_id in skill_ids:
                                if not skill_groups[skill_id]:
                                    continue
    
                                selected_for_difficulty.append(
                                    skill_groups[skill_id].pop()
                                )
                                added_question = True
    
                                if len(selected_for_difficulty) >= required_count:
                                    break
    
                            if not added_question:
                                break
    
                        selected_questions.extend(selected_for_difficulty)
    
                # -------------------------------------------------
                # VERIFY 50 QUESTIONS
                # -------------------------------------------------

                if len(selected_questions) == TOTAL_REQUIRED:

                    # Shuffle final 50 questions
                    random.shuffle(selected_questions)

                    question_ids = [
                        question.id
                        for question in selected_questions
                    ]

                    # Store selected questions in session.
                    # This guarantees that the same questions
                    # are used when the student submits.
                    request.session[
                        "assessment_question_ids"
                    ] = question_ids

                    request.session[
                        "assessment_career_id"
                    ] = selected_career.id

                    questions = selected_questions

                else:
                    questions = AssessmentQuestion.objects.none()

    # -------------------------------------------------
    # POST - SUBMIT ASSESSMENT
    # -------------------------------------------------

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

        # -------------------------------------------------
        # GET EXACT QUESTIONS SHOWN TO STUDENT
        # -------------------------------------------------

        question_ids = request.session.get(
            "assessment_question_ids",
            []
        )

        session_career_id = request.session.get(
            "assessment_career_id"
        )

        # Make sure the submitted career matches
        if str(session_career_id) != str(career_id):
            messages.error(
                request,
                "Assessment session expired. Please start again."
            )
            return redirect(
                f"/assessment/?career={career_id}"
            )

        questions = AssessmentQuestion.objects.filter(
            id__in=question_ids,
            career_paths=selected_career
        ).select_related(
            "skill"
        ).distinct()

        # Preserve the original random order
        question_map = {
            question.id: question
            for question in questions
        }

        questions = [
            question_map[qid]
            for qid in question_ids
            if qid in question_map
        ]

        total_questions = len(questions)

        if total_questions == 0:
            messages.error(
                request,
                "No assessment questions were found. Please try again."
            )
            return redirect("assessment")

        # -------------------------------------------------
        # CALCULATE SCORE
        # -------------------------------------------------

        score = 0

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

        # -------------------------------------------------
        # SAVE STUDENT ASSESSMENT
        # -------------------------------------------------

        assessment_obj, created = SkillAssessment.objects.get_or_create(
            user=request.user
        )

        assessment_obj.career_path = selected_career
        assessment_obj.career_goal = selected_career.name
        assessment_obj.save()

        # -------------------------------------------------
        # SAVE OVERALL RESULT
        # -------------------------------------------------

        result, created = AssessmentResult.objects.update_or_create(
            user=request.user,
            defaults={
                "score": score,
                "total_questions": total_questions,
                "percentage": percentage,
            }
        )

        # Remove previous answers/results
        result.answers.all().delete()
        result.skill_results.all().delete()

        # -------------------------------------------------
        # SAVE EACH ANSWER
        # -------------------------------------------------

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

        # -------------------------------------------------
        # SKILL-WISE CALCULATION
        # -------------------------------------------------

        skill_data = {}

        for question in questions:

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

        # -------------------------------------------------
        # SAVE SKILL RESULTS
        # -------------------------------------------------

        # Get all answers once
        all_answers = list(
            result.answers.select_related("question", "question__skill")
        )

        for data in skill_data.values():

            skill = data["skill"]
            total = data["total"]
            correct = data["correct"]

            skill_percentage = (
                (correct / total) * 100
                if total > 0
                else 0
            )

            # -------------------------------------------------
            # DIFFICULTY-WISE COUNTS FOR THIS SKILL
            # -------------------------------------------------

            easy_total = 0
            easy_correct = 0

            medium_total = 0
            medium_correct = 0

            hard_total = 0
            hard_correct = 0

            for answer in all_answers:

                # Only consider answers belonging to this skill
                if answer.question.skill_id != skill.id:
                    continue

                difficulty = answer.question.difficulty

                if difficulty == "easy":

                    easy_total += 1

                    if answer.is_correct:
                        easy_correct += 1

                elif difficulty == "medium":

                    medium_total += 1

                    if answer.is_correct:
                        medium_correct += 1

                elif difficulty == "hard":

                    hard_total += 1

                    if answer.is_correct:
                        hard_correct += 1

            # -------------------------------------------------
            # DIFFICULTY PERCENTAGES
            # -------------------------------------------------

            easy_percentage = (
                (easy_correct / easy_total) * 100
                if easy_total > 0
                else 0
            )

            medium_percentage = (
                (medium_correct / medium_total) * 100
                if medium_total > 0
                else 0
            )

            hard_percentage = (
                (hard_correct / hard_total) * 100
                if hard_total > 0
                else 0
            )

            # -------------------------------------------------
            # DETERMINE SKILL LEVEL
            # -------------------------------------------------

            if (
                medium_percentage >= 70
                and hard_percentage >= 70
            ):
                level = "Expert"

            elif (
                medium_percentage >= 60
                and hard_percentage >= 40
            ):
                level = "Advanced"

            elif (
                easy_percentage >= 60
                and medium_percentage >= 40
            ):
                level = "Intermediate"

            else:
                level = "Beginner"

            # -------------------------------------------------
            # SAVE RESULT
            # -------------------------------------------------

            SkillAssessmentResult.objects.create(
                result=result,
                skill=skill,
                correct_answers=correct,
                total_questions=total,
                percentage=skill_percentage,
                level=level,
            )

        # -------------------------------------------------
        # CLEAR SESSION QUESTIONS
        # -------------------------------------------------

        request.session.pop(
            "assessment_question_ids",
            None
        )

        request.session.pop(
            "assessment_career_id",
            None
        )

        # -------------------------------------------------
        # RESULT PAGE
        # -------------------------------------------------

        return redirect("assessment_result")

    # -------------------------------------------------
    # RENDER ASSESSMENT PAGE
    # -------------------------------------------------

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
        result = AssessmentResult.objects.prefetch_related(
            "skill_results__skill"
        ).get(user=request.user)

    except AssessmentResult.DoesNotExist:
        return redirect("assessment")

    skill_results = result.skill_results.all()

    return render(
        request,
        "assessment/assessment_result.html",
        {
            "result": result,
            "skill_results": skill_results,
        }
    )
@login_required
def skill_gap_analysis(request):
    from accounts.models import CareerSkill
    from .models import AssessmentResult, SkillAssessment

    try:
        result = AssessmentResult.objects.get(
            user=request.user
        )
    except AssessmentResult.DoesNotExist:
        return redirect("assessment")

    try:
        assessment = SkillAssessment.objects.get(
            user=request.user
        )
    except SkillAssessment.DoesNotExist:
        return redirect("assessment_result")

    career_path = assessment.career_path

    if not career_path:
        return redirect("assessment_result")

    # Get required skills for the selected career
    career_skills = CareerSkill.objects.filter(
        career_path=career_path
    ).select_related("skill")

    # Get student's assessment results
    skill_results = {
        item.skill_id: item
        for item in result.skill_results.select_related("skill")
    }

    level_order = {
        "Beginner": 1,
        "Intermediate": 2,
        "Advanced": 3,
        "Expert": 4,
    }

    skill_gaps = []

    for career_skill in career_skills:

        student_result = skill_results.get(
            career_skill.skill_id
        )

        student_level = (
            student_result.level
            if student_result
            else "Beginner"
        )

        required_level = career_skill.required_level

        student_value = level_order.get(
            student_level,
            1
        )

        required_value = level_order.get(
            required_level,
            1
        )

        gap = required_value - student_value

        if gap > 0:
            status = "Gap"
        else:
            status = "Achieved"

        percentage = (
            student_result.percentage
            if student_result
            else 0
        )

        skill_gaps.append({
            "skill": career_skill.skill,
            "required_level": required_level,
            "student_level": student_level,
            "gap": gap,
            "status": status,
            "percentage": percentage,
            "priority": career_skill.priority,
            "is_required": career_skill.is_required,
        })

    # Put the most important gaps first
    skill_gaps.sort(
        key=lambda item: (
            item["status"] != "Gap",
            item["priority"]
        )
    )

    return render(
        request,
        "assessment/skill_gap_analysis.html",
        {
            "career_path": career_path,
            "skill_gaps": skill_gaps,
        }
    )