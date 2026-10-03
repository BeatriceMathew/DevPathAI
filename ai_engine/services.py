import json
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
import random
from accounts.models import CareerSkill, RoadmapTopic
from assessment.models import SkillAssessment, AssessmentResult

from .prompts import ROADMAP_SYSTEM_PROMPT


load_dotenv()


def generate_ai_roadmap(user):

    # ---------------------------------------
    # 1. Get student's assessment
    # ---------------------------------------

    assessment = SkillAssessment.objects.select_related(
        "career_path"
    ).get(user=user)

    result = AssessmentResult.objects.get(
        user=user
    )

    career_path = assessment.career_path

    if not career_path:
        raise ValueError(
            "Career goal is not selected."
        )

    # ---------------------------------------
    # 2. Get career skill requirements
    # ---------------------------------------

    career_skills = CareerSkill.objects.filter(
        career_path=career_path
    ).select_related("skill")

    # ---------------------------------------
    # 3. Get student's skill results
    # ---------------------------------------

    skill_results = {
        item.skill_id: item
        for item in result.skill_results.select_related("skill")
    }

    level_order = {
        "Beginner": 1,
        "Intermediate": 2,
        "Advanced": 3,
        "Expert": 4
    }

    skills_data = []

    # ---------------------------------------
    # 4. Build AI input
    # ---------------------------------------

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

        # -----------------------------------
        # Available database topics
        # -----------------------------------

        topics = RoadmapTopic.objects.filter(
            roadmap__career_path=career_path,
            skill=career_skill.skill,
            is_active=True
        ).order_by("order")

        topic_data = []

        for topic in topics:

            topic_data.append({

                "title": topic.title,

                "description": topic.description,

                "estimated_hours": topic.estimated_hours

            })

        skills_data.append({

            "skill": career_skill.skill.name,

            "current_level": current_level,

            "percentage": percentage,

            "required_level": required_level,

            "skill_gap": gap,

            "priority": career_skill.priority,

            "required": career_skill.is_required,

            "available_topics": topic_data

        })

    # ---------------------------------------
    # 5. Prepare AI input
    # ---------------------------------------

    student_data = {

        "career_goal": career_path.name,

        "skills": skills_data

    }

    prompt = f"""
Create a personalized learning roadmap for this student.

Student information:

{json.dumps(student_data, indent=2)}

Analyze the student's skill gaps and career requirements carefully.

Create a logical learning sequence.

The roadmap should contain:
- learning phases
- topics
- projects
- resources
- estimated duration
- explanation for each phase
"""

    # ---------------------------------------
    # 6. Connect Gemini
    # ---------------------------------------

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:

        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    client = genai.Client(
        api_key=api_key
    )

    # ---------------------------------------
    # 7. JSON schema
    # ---------------------------------------

    roadmap_schema = {
        "type": "object",
        "properties": {
            "career": {
                "type": "string"
            },

            "summary": {
                "type": "string"
            },

            "phases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "phase": {
                            "type": "integer"
                        },

                        "title": {
                            "type": "string"
                        },

                        "reason": {
                            "type": "string"
                        },

                        "estimated_weeks": {
                            "type": "integer"
                        },

                        "topics": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },

                        "projects": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },

                        "resources": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },

                    "required": [
                        "phase",
                        "title",
                        "reason",
                        "estimated_weeks",
                        "topics",
                        "projects",
                        "resources"
                    ]
                }
            }
        },

        "required": [
            "career",
            "summary",
            "phases"
        ]
    }

    # ---------------------------------------
    # 8. Ask Gemini with retry
    # ---------------------------------------

    max_retries = 3

    for attempt in range(max_retries):

        try:

            response = client.models.generate_content(

                model="gemini-3.8-flash",

                contents=prompt,

                config=types.GenerateContentConfig(

                    system_instruction=ROADMAP_SYSTEM_PROMPT,

                    response_mime_type="application/json",

                    response_schema=roadmap_schema
                )
            )

            break

        except Exception as e:

            error_message = str(e)

            # Quota exceeded — do not repeatedly retry
            if "429" in error_message:
                raise

            # Temporary Gemini server problem — retry
            if "503" in error_message and attempt < max_retries - 1:

                wait_time = 2 ** attempt

                print(
                    f"Gemini temporarily unavailable. "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

            else:
                raise
    # ---------------------------------------
    # 9. Convert AI response to Python
    # ---------------------------------------

    roadmap = json.loads(
        response.text
    )

    return roadmap



# ============================================================
# GENERATE AI ASSESSMENT FOR A ROADMAP PHASE
# ============================================================

def generate_phase_assessment(user, roadmap, phase_number):
    """
    Generate exactly 10 MCQ questions for a specific roadmap phase.

    Primary model:
        gemini-3.8-flash

    Fallback model:
        gemini-3.5-flash-lite

    The assessment is generated only from the selected phase.
    """

    # ---------------------------------------------------------
    # 1. Get selected phase
    # ---------------------------------------------------------

    phases = roadmap.roadmap_data.get("phases", [])

    selected_phase = None

    for phase in phases:
        if phase.get("phase") == phase_number:
            selected_phase = phase
            break

    if not selected_phase:
        raise ValueError(
            f"Phase {phase_number} was not found in the roadmap."
        )

    phase_title = selected_phase.get(
        "title",
        f"Phase {phase_number}"
    )

    topics = selected_phase.get("topics", [])
    projects = selected_phase.get("projects", [])
    resources = selected_phase.get("resources", [])

    # ---------------------------------------------------------
    # 2. Build prompt
    # ---------------------------------------------------------

    prompt = f"""
You are generating an assessment for a personalized developer
learning roadmap.

ROADMAP PHASE:
Phase {phase_number}: {phase_title}

TOPICS COVERED IN THIS PHASE:
{json.dumps(topics, indent=2)}

PROJECTS COVERED IN THIS PHASE:
{json.dumps(projects, indent=2)}

RESOURCES COVERED IN THIS PHASE:
{json.dumps(resources, indent=2)}

IMPORTANT RULES:

1. Generate EXACTLY 10 multiple-choice questions.
2. Every question must have exactly 4 options.
3. Only one option must be correct.
4. Use Option A, B, C and D.
5. Questions must be based ONLY on the content of this phase.
6. Do NOT ask questions about later roadmap phases.
7. Do NOT ask questions about unrelated technologies.
8. Do NOT introduce topics that are not covered by this phase.
9. Questions should test actual understanding, not only memorization.
10. Include a mixture of Easy, Medium and Hard questions.
11. Include practical/developer-oriented questions where appropriate.
12. Every question must have a topic.
13. The assessment should be suitable for a student learning this phase.
14. The correct answer must be one of A, B, C or D.
15. The assessment will use 70% as the passing percentage.

Return ONLY valid JSON matching the provided schema.
"""

    # ---------------------------------------------------------
    # 3. Check Gemini API key
    # ---------------------------------------------------------

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    # ---------------------------------------------------------
    # 4. Create Gemini client
    # ---------------------------------------------------------

    client = genai.Client(api_key=api_key)

    # ---------------------------------------------------------
    # 5. JSON schema
    # ---------------------------------------------------------

    assessment_schema = {
        "type": "object",
        "properties": {
            "phase": {
                "type": "integer"
            },
            "phase_title": {
                "type": "string"
            },
            "questions": {
                "type": "array",
                "minItems": 10,
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string"
                        },
                        "option_a": {
                            "type": "string"
                        },
                        "option_b": {
                            "type": "string"
                        },
                        "option_c": {
                            "type": "string"
                        },
                        "option_d": {
                            "type": "string"
                        },
                        "correct_answer": {
                            "type": "string",
                            "enum": [
                                "A",
                                "B",
                                "C",
                                "D"
                            ]
                        },
                        "topic": {
                            "type": "string"
                        },
                        "difficulty": {
                            "type": "string",
                            "enum": [
                                "easy",
                                "medium",
                                "hard"
                            ]
                        }
                    },
                    "required": [
                        "question",
                        "option_a",
                        "option_b",
                        "option_c",
                        "option_d",
                        "correct_answer",
                        "topic",
                        "difficulty"
                    ]
                }
            }
        },
        "required": [
            "phase",
            "phase_title",
            "questions"
        ]
    }

    # ---------------------------------------------------------
    # 6. Models
    # ---------------------------------------------------------

    models = [
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite"
    ]

    last_error = None

    # ---------------------------------------------------------
    # 7. Try primary model and fallback model
    # ---------------------------------------------------------

    for model_index, model_name in enumerate(models):

        # Primary model gets 2 attempts.
        # Fallback model also gets 2 attempts.
        max_retries = 2

        print(
            f"\nTrying Gemini model: {model_name}"
        )

        for attempt in range(max_retries):

            try:

                print(
                    f"Generating Phase {phase_number} assessment..."
                    f" Model={model_name}, "
                    f"Attempt={attempt + 1}/{max_retries}"
                )

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=ROADMAP_SYSTEM_PROMPT,
                        response_mime_type="application/json",
                        response_schema=assessment_schema
                    )
                )

                # -------------------------------------------------
                # 8. Parse JSON
                # -------------------------------------------------

                try:
                    assessment = json.loads(response.text)

                except json.JSONDecodeError as e:
                    raise Exception(
                        f"Gemini returned invalid JSON: {str(e)}"
                    )

                # -------------------------------------------------
                # 9. Validate questions
                # -------------------------------------------------

                questions = assessment.get(
                    "questions",
                    []
                )

                if len(questions) != 10:
                    raise Exception(
                        f"Gemini generated {len(questions)} "
                        f"questions instead of exactly 10."
                    )

                required_fields = [
                    "question",
                    "option_a",
                    "option_b",
                    "option_c",
                    "option_d",
                    "correct_answer",
                    "topic",
                    "difficulty"
                ]

                for index, question in enumerate(questions):

                    for field in required_fields:

                        if field not in question:
                            raise Exception(
                                f"Question {index + 1} "
                                f"is missing field: {field}"
                            )

                    if question["correct_answer"] not in [
                        "A",
                        "B",
                        "C",
                        "D"
                    ]:
                        raise Exception(
                            f"Question {index + 1} "
                            f"has an invalid correct answer."
                        )

                    if question["difficulty"] not in [
                        "easy",
                        "medium",
                        "hard"
                    ]:
                        raise Exception(
                            f"Question {index + 1} "
                            f"has an invalid difficulty."
                        )

                # -------------------------------------------------
                # 10. Force correct phase information
                # -------------------------------------------------

                assessment["phase"] = phase_number
                assessment["phase_title"] = phase_title

                print(
                    f"Phase {phase_number} assessment generated "
                    f"successfully using {model_name}."
                )

                return assessment

            except Exception as e:

                last_error = e
                error_message = str(e)

                print(
                    f"Gemini request failed "
                    f"(model={model_name}, "
                    f"attempt={attempt + 1}/{max_retries}): "
                    f"{error_message}"
                )

                # -------------------------------------------------
                # 11. Handle rate limit
                # -------------------------------------------------

                if "429" in error_message:

                    print(
                        f"Rate limit detected for {model_name}."
                    )

                    # Try next model
                    break

                # -------------------------------------------------
                # 12. Handle temporary 503
                # -------------------------------------------------

                if "503" in error_message:

                    if attempt < max_retries - 1:

                        # 5 seconds, then 10 seconds
                        base_wait = 5 * (2 ** attempt)

                        # Small random delay prevents
                        # repeated requests at exactly
                        # the same time.
                        jitter = random.uniform(0, 2)

                        wait_time = base_wait + jitter

                        print(
                            f"{model_name} is temporarily "
                            f"unavailable."
                        )

                        print(
                            f"Retrying in "
                            f"{wait_time:.1f} seconds..."
                        )

                        time.sleep(wait_time)

                        continue

                    else:

                        print(
                            f"{model_name} failed after "
                            f"{max_retries} attempts."
                        )

                        # Move to fallback model
                        break

                # -------------------------------------------------
                # 13. Other errors
                # -------------------------------------------------

                raise

    # ---------------------------------------------------------
    # 14. Both models failed
    # ---------------------------------------------------------

    raise Exception(
        "Gemini could not generate the Phase "
        f"{phase_number} assessment.\n\n"
        f"Last error: {last_error}"
    )