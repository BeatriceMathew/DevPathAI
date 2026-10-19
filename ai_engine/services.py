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

import logging

from groq import Groq
from ollama import Client as OllamaClient

logger = logging.getLogger(__name__)
load_dotenv()



def generate_ai_roadmap(user):
    import json
    import os

    from groq import Groq
    from ollama import Client as OllamaClient
    from google import genai
    from google.genai import types

    from accounts.models import CareerSkill, RoadmapTopic
    from assessment.models import SkillAssessment, AssessmentResult

    # 1. Retrieve assessment and career path
    assessment = (
        SkillAssessment.objects
        .select_related("career_path")
        .get(user=user)
    )

    result = (
        AssessmentResult.objects
        .filter(user=user)
        .order_by("-completed_at", "-id")
        .first()
    )

    if result is None:
        raise ValueError(
            "Please complete the skill assessment first."
        )

    career_path = assessment.career_path

    if career_path is None:
        raise ValueError(
            "Please select a career path first."
        )

    # 2. Build the student's skill-gap information
    career_skills = (
        CareerSkill.objects
        .filter(career_path=career_path)
        .select_related("skill")
    )

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

    skills_data = []

    for item in career_skills:
        student_result = skill_results.get(item.skill_id)

        current_level = (
            student_result.level
            if student_result else "Beginner"
        )
        percentage = (
            student_result.percentage
            if student_result else 0
        )

        gap = max(
            level_order.get(item.required_level, 1)
            - level_order.get(current_level, 1),
            0,
        )

        topics = RoadmapTopic.objects.filter(
            roadmap__career_path=career_path,
            skill=item.skill,
            is_active=True,
        ).order_by("order")

        skills_data.append({
            "skill": item.skill.name,
            "current_level": current_level,
            "percentage": percentage,
            "required_level": item.required_level,
            "skill_gap": gap,
            "priority": item.priority,
            "required": item.is_required,
            "available_topics": [
                {
                    "title": topic.title,
                    "description": topic.description,
                    "estimated_hours": topic.estimated_hours,
                }
                for topic in topics
            ],
        })

    student_data = {
        "career_goal": career_path.name,
        "skills": skills_data,
    }

    prompt = f"""
Create a personalized developer learning roadmap.

Student data:
{json.dumps(student_data, indent=2)}

Analyze the student's skill gaps and career requirements.
Create a logical learning sequence from foundational to
advanced concepts. Prioritize important skill gaps.

Return ONLY valid JSON in this structure:
{{
  "career": "string",
  "summary": "string",
  "phases": [
    {{
      "phase": 1,
      "title": "string",
      "reason": "string",
      "estimated_weeks": 2,
      "topics": ["topic"],
      "projects": ["project"],
      "resources": ["resource"]
    }}
  ]
}}

Include practical projects and relevant learning resources.
Do not invent assessment scores.
"""

    schema = {
        "type": "object",
        "properties": {
            "career": {"type": "string"},
            "summary": {"type": "string"},
            "phases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "phase": {"type": "integer"},
                        "title": {"type": "string"},
                        "reason": {"type": "string"},
                        "estimated_weeks": {"type": "integer"},
                        "topics": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "projects": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "resources": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "phase", "title", "reason",
                        "estimated_weeks", "topics",
                        "projects", "resources",
                    ],
                },
            },
        },
        "required": ["career", "summary", "phases"],
    }

    def validate_response(raw):
        data = json.loads(raw)

        if not isinstance(data, dict):
            raise ValueError("Response is not a JSON object.")

        phases = data.get("phases")
        if not isinstance(phases, list) or not phases:
            raise ValueError("No roadmap phases were generated.")

        for index, phase in enumerate(phases, start=1):
            for field in (
                "title", "reason", "estimated_weeks",
                "topics", "projects", "resources",
            ):
                if field not in phase:
                    raise ValueError(
                        f"Phase {index} is missing {field}."
                    )

            for field in ("topics", "projects", "resources"):
                if not isinstance(phase[field], list):
                    raise ValueError(
                        f"Phase {index}: {field} must be a list."
                    )

            phase["phase"] = index

        data["career"] = career_path.name

        if not isinstance(data.get("summary"), str):
            raise ValueError("Roadmap summary is missing.")

        return data

    errors = []

    # 3. PROVIDER 1: GROQ
    if os.getenv("GROQ_API_KEY"):
        try:
            print("Trying Groq for roadmap generation...")

            client = Groq(
                api_key=os.getenv("GROQ_API_KEY")
            )

            response = client.chat.completions.create(
                model=os.getenv(
                    "GROQ_MODEL",
                    "openai/gpt-oss-20b",
                ),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Generate a useful developer roadmap. "
                            "Return only valid JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            roadmap = validate_response(
                response.choices[0].message.content
            )

            print("Roadmap generated successfully with Groq.")
            return roadmap

        except Exception as exc:
            errors.append(f"Groq: {exc}")
            print(f"Groq failed: {type(exc).__name__}: {exc}")
    else:
        errors.append("Groq: GROQ_API_KEY is missing.")

    # 4. PROVIDER 2: LOCAL OLLAMA
    try:
        print("Trying local Ollama for roadmap generation...")

        client = OllamaClient(
            host=os.getenv(
                "OLLAMA_HOST",
                "http://localhost:11434",
            )
        )

        response = client.chat(
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate a useful developer roadmap. "
                        "Return JSON matching the required schema."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            format=schema,
            options={"temperature": 0.3},
        )

        roadmap = validate_response(
            response.message.content
        )

        print("Roadmap generated successfully with Ollama.")
        return roadmap

    except Exception as exc:
        errors.append(f"Ollama: {exc}")
        print(f"Ollama failed: {type(exc).__name__}: {exc}")

    # 5. PROVIDER 3: GEMINI
    if os.getenv("GEMINI_API_KEY"):
        try:
            print("Trying Gemini for roadmap generation...")

            client = genai.Client(
                api_key=os.getenv("GEMINI_API_KEY")
            )

            response = client.models.generate_content(
                model=os.getenv(
                    "GEMINI_MODEL",
                    "gemini-3.8-flash",
                ),
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                ),
            )

            roadmap = validate_response(response.text)

            print("Roadmap generated successfully with Gemini.")
            return roadmap

        except Exception as exc:
            errors.append(f"Gemini: {exc}")
            print(f"Gemini failed: {type(exc).__name__}: {exc}")
    else:
        errors.append("Gemini: GEMINI_API_KEY is missing.")

    # All providers failed
    raise RuntimeError(
        "All AI providers failed:\n" + "\n".join(errors)
    )


# ============================================================
# GENERATE AI ASSESSMENT FOR A ROADMAP PHASE
# ============================================================

def generate_phase_assessment(user, roadmap, phase_number):
    """
    Generate 10 MCQs for a specific roadmap phase.

    Provider priority:
    1. Groq
    2. Ollama
    3. Gemini
    """

    # --------------------------------------------------
    # 1. Get the selected phase
    # --------------------------------------------------
    roadmap_data = roadmap.roadmap_data
    phases = roadmap_data.get("phases", [])

    phase_data = next(
        (
            phase for phase in phases
            if str(phase.get("phase")) == str(phase_number)
        ),
        None
    )

    if not phase_data:
        raise ValueError(
            f"Phase {phase_number} was not found in the roadmap."
        )

    phase_title = phase_data.get("title", f"Phase {phase_number}")
    topics = phase_data.get("topics", [])
    projects = phase_data.get("projects", [])
    resources = phase_data.get("resources", [])

    # --------------------------------------------------
    # 2. JSON schema for the assessment
    # --------------------------------------------------
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
                        "question": {"type": "string"},
                        "option_a": {"type": "string"},
                        "option_b": {"type": "string"},
                        "option_c": {"type": "string"},
                        "option_d": {"type": "string"},
                        "correct_answer": {
                            "type": "string",
                            "enum": ["A", "B", "C", "D"]
                        },
                        "topic": {"type": "string"},
                        "difficulty": {
                            "type": "string",
                            "enum": ["easy", "medium", "hard"]
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
                    ],
                    "additionalProperties": False
                }
            }
        },
        "required": ["phase", "phase_title", "questions"],
        "additionalProperties": False
    }

    # --------------------------------------------------
    # 3. Assessment prompt
    # --------------------------------------------------
    prompt = f"""
Generate a technical assessment for the selected roadmap phase.

CAREER:
{roadmap_data.get("career", "Software Developer")}

PHASE NUMBER:
{phase_number}

PHASE TITLE:
{phase_title}

PHASE TOPICS:
{json.dumps(topics, ensure_ascii=False)}

PHASE PROJECTS:
{json.dumps(projects, ensure_ascii=False)}

PHASE RESOURCES:
{json.dumps(resources, ensure_ascii=False)}

STRICT RULES:
1. Generate EXACTLY 10 multiple-choice questions.
2. Each question must have exactly four options: A, B, C and D.
3. Exactly one option must be correct.
4. correct_answer must be A, B, C or D.
5. Every question must include its topic and difficulty.
6. Difficulty must be easy, medium or hard.
7. Include a mixture of easy, medium and hard questions.
8. Questions must be based ONLY on the selected phase topics,
   projects and resources.
9. Do not include technologies or concepts from later phases.
10. Questions should test understanding and practical application.
11. Avoid duplicate or ambiguous questions.
12. Return only valid JSON matching the provided schema.
13. The phase number must be {phase_number}.
14. The phase title must be "{phase_title}".

Return this structure:
{{
    "phase": {phase_number},
    "phase_title": "{phase_title}",
    "questions": [
        {{
            "question": "Question text",
            "option_a": "Option A",
            "option_b": "Option B",
            "option_c": "Option C",
            "option_d": "Option D",
            "correct_answer": "A",
            "topic": "Topic name",
            "difficulty": "easy"
        }}
    ]
}}
"""

    # --------------------------------------------------
    # 4. Validate provider output
    # --------------------------------------------------
    def validate_assessment(raw_response):
        if isinstance(raw_response, str):
            # Handle a possible JSON markdown code fence.
            cleaned = raw_response.strip()

            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
                if cleaned.rstrip().endswith("```"):
                    cleaned = cleaned.rstrip()[:-3].strip()

            result = json.loads(cleaned)
        elif isinstance(raw_response, dict):
            result = raw_response
        else:
            raise ValueError("The AI returned an unsupported response.")

        questions = result.get("questions")

        if not isinstance(questions, list) or len(questions) != 10:
            raise ValueError(
                "The AI must return exactly 10 assessment questions."
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

        valid_difficulties = {"easy", "medium", "hard"}

        for index, question in enumerate(questions, start=1):
            if not isinstance(question, dict):
                raise ValueError(f"Question {index} is not a valid object.")

            for field in required_fields:
                if not isinstance(question.get(field), str):
                    raise ValueError(
                        f"Question {index} has an invalid or missing {field}."
                    )

                if not question[field].strip():
                    raise ValueError(
                        f"Question {index} has an empty {field}."
                    )

            question["correct_answer"] = (
                question["correct_answer"].strip().upper()
            )

            if question["correct_answer"] not in {"A", "B", "C", "D"}:
                raise ValueError(
                    f"Question {index} has an invalid correct answer."
                )

            question["difficulty"] = (
                question["difficulty"].strip().lower()
            )

            if question["difficulty"] not in valid_difficulties:
                raise ValueError(
                    f"Question {index} has an invalid difficulty."
                )

        # Use the actual phase from the user's saved roadmap.
        result["phase"] = int(phase_number)
        result["phase_title"] = phase_title
        result["questions"] = questions

        return result

    errors = []

    # --------------------------------------------------
    # 5. Provider 1: Groq
    # --------------------------------------------------
    try:
        groq_api_key = os.getenv("GROQ_API_KEY")

        if not groq_api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        client = Groq(api_key=groq_api_key)

        response = client.chat.completions.create(
            model=os.getenv(
                "GROQ_MODEL",
                "openai/gpt-oss-20b"
            ),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate accurate technical MCQ assessments. "
                        "Return only valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )

        raw = response.choices[0].message.content
        assessment = validate_assessment(raw)

        logger.info("Phase assessment generated using Groq.")
        return assessment

    except Exception as e:
        errors.append(f"Groq: {type(e).__name__}: {e}")
        logger.warning("Groq assessment generation failed: %s", e)

    # --------------------------------------------------
    # 6. Provider 2: Ollama (local model)
    # --------------------------------------------------
    try:
        client = OllamaClient(
            host=os.getenv(
                "OLLAMA_HOST",
                "http://localhost:11434"
            )
        )

        response = client.chat(
            model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate accurate technical MCQ assessments. "
                        "Follow the supplied JSON schema exactly."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            format=assessment_schema,
            options={"temperature": 0.2}
        )

        raw = response["message"]["content"]
        assessment = validate_assessment(raw)

        logger.info("Phase assessment generated using Ollama.")
        return assessment

    except Exception as e:
        errors.append(f"Ollama: {type(e).__name__}: {e}")
        logger.warning("Ollama assessment generation failed: %s", e)

    # --------------------------------------------------
    # 7. Provider 3: Gemini
    # --------------------------------------------------
    try:
        gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        client = genai.Client(api_key=gemini_api_key)

        response = client.models.generate_content(
            model=os.getenv(
                "GEMINI_MODEL",
                "gemini-3.8-flash"
            ),
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=assessment_schema,
                temperature=0.2
            )
        )

        raw = response.text
        assessment = validate_assessment(raw)

        logger.info("Phase assessment generated using Gemini.")
        return assessment

    except Exception as e:
        errors.append(f"Gemini: {type(e).__name__}: {e}")
        logger.warning("Gemini assessment generation failed: %s", e)

    # --------------------------------------------------
    # 8. All providers failed
    # --------------------------------------------------
    raise RuntimeError(
        "All AI providers failed to generate the phase assessment. "
        + " | ".join(errors)
    )