from django.core.management.base import BaseCommand
from assessment.models import AssessmentQuestion
from accounts.models import Skill, CareerPath


class Command(BaseCommand):

    help = "Add remaining Python Developer assessment questions"

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.SUCCESS(
                "Python Developer assessment import started..."
            )
        )

        # ---------------------------------------------------------
        # GET CAREER PATH
        # ---------------------------------------------------------

        career = CareerPath.objects.filter(
            name="Python Developer"
        ).first()

        if not career:
            self.stdout.write(
                self.style.ERROR(
                    "Python Developer career path does not exist."
                )
            )
            return

        # ---------------------------------------------------------
        # GET SKILLS
        # ---------------------------------------------------------

        skill_names = [
            "Python",
            "Django",
            "FastAPI",
            "SQL / Database",
            "REST API",
            "Git & GitHub",
        ]

        skills = {}

        for name in skill_names:

            skill = Skill.objects.filter(
                name=name
            ).first()

            if not skill:
                self.stdout.write(
                    self.style.ERROR(
                        f"Skill '{name}' does not exist."
                    )
                )
                return

            skills[name] = skill

        # ---------------------------------------------------------
        # REMAINING 36 QUESTIONS
        # 12 MEDIUM + 24 HARD
        # ---------------------------------------------------------

        questions = [

            # =====================================================
            # MEDIUM - 15 TO 26
            # =====================================================

            {
                "question": "What is FastAPI?",
                "option_a": "A Python web framework for building APIs",
                "option_b": "A database management system",
                "option_c": "A version control system",
                "option_d": "A frontend JavaScript library",
                "correct_answer": "A",
                "category": "frameworks",
                "difficulty": "easy",
                "skill": "FastAPI",
            },
            {
                "question": "Which HTTP status code indicates that a request was successful?",
                "option_a": "200 OK",
                "option_b": "404 Not Found",
                "option_c": "500 Internal Server Error",
                "option_d": "401 Unauthorized",
                "correct_answer": "A",
                "category": "frameworks",
                "difficulty": "medium",
                "skill": "REST API",
            },
            {
                "question": "Which HTTP status code is commonly returned when a new resource is successfully created?",
                "option_a": "200 OK",
                "option_b": "201 Created",
                "option_c": "404 Not Found",
                "option_d": "500 Internal Server Error",
                "correct_answer": "B",
                "category": "frameworks",
                "difficulty": "medium",
                "skill": "REST API",
            },
            {
                "question": "Which HTTP method is generally considered idempotent and is commonly used to completely replace a resource?",
                "option_a": "POST",
                "option_b": "GET",
                "option_c": "PUT",
                "option_d": "PATCH",
                "correct_answer": "C",
                "category": "frameworks",
                "difficulty": "hard",
                "skill": "REST API",
            },
            {
                "question": "Which HTTP status code is commonly returned when a FastAPI request is successfully processed and returns a new resource?",
                "option_a": "200 OK",
                "option_b": "201 Created",
                "option_c": "404 Not Found",
                "option_d": "500 Internal Server Error",
                "correct_answer": "B",
                "category": "frameworks",
                "difficulty": "medium",
                "skill": "FastAPI",
            },
            {
                "question": "What is Git primarily used for?",
                "option_a": "Version control",
                "option_b": "Database management",
                "option_c": "Web page styling",
                "option_d": "Operating system management",
                "correct_answer": "A",
                "category": "tools",
                "difficulty": "easy",
                "skill": "Git & GitHub",
            },
            {
                "question": "Which Git command is used to upload local commits to a remote repository?",
                "option_a": "git pull",
                "option_b": "git push",
                "option_c": "git clone",
                "option_d": "git status",
                "correct_answer": "B",
                "category": "tools",
                "difficulty": "medium",
                "skill": "Git & GitHub",
            },
            {
                "question": "What is the main purpose of resolving a Git merge conflict?",
                "option_a": "To delete the conflicting branch",
                "option_b": "To remove the Git repository",
                "option_c": "To decide how conflicting changes should be combined",
                "option_d": "To create a new remote repository",
                "correct_answer": "C",
                "category": "tools",
                "difficulty": "hard",
                "skill": "Git & GitHub",
            },
            {
                "question": "What is the purpose of a Python virtual environment?",
                "option_a": "To isolate project dependencies",
                "option_b": "To increase internet speed",
                "option_c": "To convert Python into Java",
                "option_d": "To create a database",
                "correct_answer": "A",
                "category": "programming",
                "difficulty": "medium",
                "skill": "Python",
            },

            {
                "question": "What will be the output of [x * 2 for x in [1, 2, 3, 4]]?",
                "option_a": "[1, 2, 3, 4]",
                "option_b": "[2, 4, 6, 8]",
                "option_c": "[1, 4, 9, 16]",
                "option_d": "[3, 4, 5, 6]",
                "correct_answer": "B",
                "category": "programming",
                "difficulty": "medium",
                "skill": "Python",
            },

            {
                "question": "Which Python data structure does not allow duplicate elements?",
                "option_a": "List",
                "option_b": "Tuple",
                "option_c": "Set",
                "option_d": "Dictionary",
                "correct_answer": "C",
                "category": "programming",
                "difficulty": "medium",
                "skill": "Python",
            },

            {
                "question": "Which Django component is primarily responsible for handling a request and returning a response?",
                "option_a": "Model",
                "option_b": "View",
                "option_c": "Migration",
                "option_d": "Admin",
                "correct_answer": "B",
                "category": "frameworks",
                "difficulty": "medium",
                "skill": "Django",
            },

            {
                "question": "What is Django ORM used for?",
                "option_a": "Managing database operations using Python objects",
                "option_b": "Creating CSS files",
                "option_c": "Managing Git branches",
                "option_d": "Encrypting passwords manually",
                "correct_answer": "A",
                "category": "frameworks",
                "difficulty": "medium",
                "skill": "Django",
            },

            {
                "question": "Which Django command creates migration files based on model changes?",
                "option_a": "python manage.py migrate",
                "option_b": "python manage.py makemigrations",
                "option_c": "python manage.py migration",
                "option_d": "python manage.py models",
                "correct_answer": "B",
                "category": "frameworks",
                "difficulty": "medium",
                "skill": "Django",
            },

            {
                "question": "What is the main purpose of a Pydantic model in FastAPI?",
                "option_a": "Data validation and serialization",
                "option_b": "Git management",
                "option_c": "Database indexing",
                "option_d": "CSS rendering",
                "correct_answer": "A",
                "category": "frameworks",
                "difficulty": "medium",
                "skill": "FastAPI",
            },

            {
                "question": "Which HTTP method is normally used to create a resource through a REST API?",
                "option_a": "GET",
                "option_b": "POST",
                "option_c": "DELETE",
                "option_d": "HEAD",
                "correct_answer": "B",
                "category": "frameworks",
                "difficulty": "medium",
                "skill": "REST API",
            },

            {
                "question": "Which SQL clause is used to filter rows based on a condition?",
                "option_a": "ORDER BY",
                "option_b": "WHERE",
                "option_c": "GROUP BY",
                "option_d": "JOIN",
                "correct_answer": "B",
                "category": "databases",
                "difficulty": "medium",
                "skill": "SQL / Database",
            },

            {
                "question": "Which SQL operation is used to combine related records from two tables?",
                "option_a": "JOIN",
                "option_b": "SORT",
                "option_c": "FILTER",
                "option_d": "INDEX",
                "correct_answer": "A",
                "category": "databases",
                "difficulty": "medium",
                "skill": "SQL / Database",
            },

            {
                "question": "Which Git command creates a new commit from staged changes?",
                "option_a": "git push",
                "option_b": "git commit",
                "option_c": "git clone",
                "option_d": "git fetch",
                "correct_answer": "B",
                "category": "tools",
                "difficulty": "medium",
                "skill": "Git & GitHub",
            },

            {
                "question": "What does git pull generally do?",
                "option_a": "Deletes the remote repository",
                "option_b": "Retrieves and integrates changes from a remote repository",
                "option_c": "Creates a new repository",
                "option_d": "Deletes the current branch",
                "correct_answer": "B",
                "category": "tools",
                "difficulty": "medium",
                "skill": "Git & GitHub",
            },

            # =====================================================
            # HARD - 27 TO 50
            # =====================================================

            {
                "question": "What will be the output of a function that uses a mutable default list and appends an item on every call?",
                "option_a": "[1] and [2]",
                "option_b": "[1] and [1, 2]",
                "option_c": "[] and []",
                "option_d": "It always raises an error",
                "correct_answer": "B",
                "category": "programming",
                "difficulty": "hard",
                "skill": "Python",
            },

            {
                "question": "What is the primary purpose of a Python decorator?",
                "option_a": "Modify or extend the behavior of a function or class",
                "option_b": "Create a database table",
                "option_c": "Install Python packages",
                "option_d": "Create a virtual machine",
                "correct_answer": "A",
                "category": "programming",
                "difficulty": "hard",
                "skill": "Python",
            },

            {
                "question": "Which keyword is commonly used to create a generator function?",
                "option_a": "return",
                "option_b": "yield",
                "option_c": "generate",
                "option_d": "next",
                "correct_answer": "B",
                "category": "programming",
                "difficulty": "hard",
                "skill": "Python",
            },

            {
                "question": "What is the main advantage of a generator when processing a large amount of data?",
                "option_a": "It stores all values permanently",
                "option_b": "It produces values lazily and can reduce memory usage",
                "option_c": "It automatically uses multiple CPUs",
                "option_d": "It converts data to SQL",
                "correct_answer": "B",
                "category": "programming",
                "difficulty": "hard",
                "skill": "Python",
            },

            {
                "question": "Which exception is commonly raised when Python recursion exceeds its maximum recursion depth?",
                "option_a": "MemoryError",
                "option_b": "RecursionError",
                "option_c": "RuntimeError only",
                "option_d": "StackError",
                "correct_answer": "B",
                "category": "programming",
                "difficulty": "hard",
                "skill": "Python",
            },

            {
                "question": "What is the purpose of __init__.py in a Python package?",
                "option_a": "It can initialize the package and traditionally identify a directory as a package",
                "option_b": "It starts the Django server",
                "option_c": "It creates a virtual environment",
                "option_d": "It compiles Python code",
                "correct_answer": "A",
                "category": "programming",
                "difficulty": "hard",
                "skill": "Python",
            },

            {
                "question": "What is the purpose of select_related() in Django?",
                "option_a": "To efficiently retrieve related objects using SQL joins for suitable relationships",
                "option_b": "To delete related objects",
                "option_c": "To create migrations",
                "option_d": "To validate forms",
                "correct_answer": "A",
                "category": "frameworks",
                "difficulty": "hard",
                "skill": "Django",
            },

            {
                "question": "What is the main purpose of prefetch_related() in Django?",
                "option_a": "To efficiently retrieve related objects using additional queries",
                "option_b": "To create database tables",
                "option_c": "To delete unused records",
                "option_d": "To create URL patterns",
                "correct_answer": "A",
                "category": "frameworks",
                "difficulty": "hard",
                "skill": "Django",
            },

            {
                "question": "Which Django security mechanism protects forms against Cross-Site Request Forgery?",
                "option_a": "CSRF protection",
                "option_b": "ORM",
                "option_c": "URL dispatcher",
                "option_d": "Template inheritance",
                "correct_answer": "A",
                "category": "frameworks",
                "difficulty": "hard",
                "skill": "Django",
            },

            {
                "question": "What is the purpose of transaction.atomic() in Django?",
                "option_a": "To execute a group of database operations as one transaction",
                "option_b": "To create database models",
                "option_c": "To cache web pages",
                "option_d": "To validate HTML",
                "correct_answer": "A",
                "category": "frameworks",
                "difficulty": "hard",
                "skill": "Django",
            },

            {
                "question": "Why are database indexes used?",
                "option_a": "To improve the performance of suitable data retrieval operations",
                "option_b": "To eliminate all duplicate records",
                "option_c": "To replace primary keys",
                "option_d": "To encrypt database tables",
                "correct_answer": "A",
                "category": "databases",
                "difficulty": "hard",
                "skill": "SQL / Database",
            },

            {
                "question": "What is the main purpose of database normalization?",
                "option_a": "Reduce data redundancy and update anomalies",
                "option_b": "Increase duplicate records",
                "option_c": "Encrypt data",
                "option_d": "Increase network bandwidth",
                "correct_answer": "A",
                "category": "databases",
                "difficulty": "hard",
                "skill": "SQL / Database",
            },

            {
                "question": "What does atomicity mean in a database transaction?",
                "option_a": "All operations succeed or none of them are committed",
                "option_b": "Every operation runs simultaneously",
                "option_c": "Data is always encrypted",
                "option_d": "Only one user can access the database",
                "correct_answer": "A",
                "category": "databases",
                "difficulty": "hard",
                "skill": "SQL / Database",
            },

            {
                "question": "What is one major trade-off of adding database indexes?",
                "option_a": "They can improve reads but require additional storage and can add overhead to writes",
                "option_b": "They always slow down reads",
                "option_c": "They eliminate the need for a database",
                "option_d": "They guarantee constant-time queries",
                "correct_answer": "A",
                "category": "databases",
                "difficulty": "hard",
                "skill": "SQL / Database",
            },

            {
                "question": "Which query pattern can find records in one table that have no matching record in another table?",
                "option_a": "LEFT JOIN with a NULL check on the right table",
                "option_b": "ORDER BY",
                "option_c": "GROUP BY only",
                "option_d": "INSERT",
                "correct_answer": "A",
                "category": "databases",
                "difficulty": "hard",
                "skill": "SQL / Database",
            },

            {
                "question": "What is dependency injection commonly used for in FastAPI?",
                "option_a": "Providing reusable dependencies such as authentication or database sessions",
                "option_b": "Creating CSS files",
                "option_c": "Managing Git commits",
                "option_d": "Creating database indexes automatically",
                "correct_answer": "A",
                "category": "frameworks",
                "difficulty": "hard",
                "skill": "FastAPI",
            },

            {
                "question": "What does a Pydantic model provide in a FastAPI application?",
                "option_a": "Data validation and serialization based on declared fields",
                "option_b": "Git branch management",
                "option_c": "Database indexing",
                "option_d": "HTML styling",
                "correct_answer": "A",
                "category": "frameworks",
                "difficulty": "hard",
                "skill": "FastAPI",
            },
            

            {
                "question": "Why can asynchronous programming be useful in FastAPI for I/O-bound operations?",
                "option_a": "It can allow other tasks to progress while waiting for I/O",
                "option_b": "It automatically makes CPU-heavy operations parallel",
                "option_c": "It eliminates database requirements",
                "option_d": "It guarantees every request finishes faster",
                "correct_answer": "A",
                "category": "frameworks",
                "difficulty": "hard",
                "skill": "FastAPI",
            },

            {
                "question": "In REST API design, what is PUT generally used for?",
                "option_a": "Retrieving a resource",
                "option_b": "Replacing or updating a resource at a known URI",
                "option_c": "Deleting a resource",
                "option_d": "Authenticating a user",
                "correct_answer": "B",
                "category": "frameworks",
                "difficulty": "hard",
                "skill": "REST API",
            },

            {
                "question": "What does HTTP status code 401 generally indicate?",
                "option_a": "Resource not found",
                "option_b": "Authentication is required or has failed",
                "option_c": "Successful request",
                "option_d": "Internal server error",
                "correct_answer": "B",
                "category": "frameworks",
                "difficulty": "hard",
                "skill": "REST API",
            },

            {
                "question": "Why is pagination used in REST APIs?",
                "option_a": "To divide a large result set into smaller responses",
                "option_b": "To encrypt API requests",
                "option_c": "To eliminate database queries",
                "option_d": "To delete old records",
                "correct_answer": "A",
                "category": "frameworks",
                "difficulty": "hard",
                "skill": "REST API",
            },

            {
                "question": "What does git rebase generally do?",
                "option_a": "Reapplies commits onto a different base commit",
                "option_b": "Deletes the Git repository",
                "option_c": "Downloads a repository",
                "option_d": "Creates a Python environment",
                "correct_answer": "A",
                "category": "tools",
                "difficulty": "hard",
                "skill": "Git & GitHub",
            },

            {
                "question": "What is the purpose of git cherry-pick?",
                "option_a": "Apply the changes from a specific existing commit to the current branch",
                "option_b": "Delete a commit permanently",
                "option_c": "Clone a repository",
                "option_d": "Delete all branches",
                "correct_answer": "A",
                "category": "tools",
                "difficulty": "hard",
                "skill": "Git & GitHub",
            },

            {
                "question": "A Git merge produces a conflict. What should you normally do?",
                "option_a": "Delete the repository",
                "option_b": "Resolve the conflicting files, stage them, and complete the merge",
                "option_c": "Run git clone again",
                "option_d": "Restart the computer",
                "correct_answer": "B",
                "category": "tools",
                "difficulty": "hard",
                "skill": "Git & GitHub",
            },
        ]

        # ---------------------------------------------------------
        # ADD QUESTIONS
        # ---------------------------------------------------------

        added_count = 0
        skipped_count = 0

        for data in questions:

            skill = skills[data["skill"]]

            # Avoid duplicate questions
            existing = AssessmentQuestion.objects.filter(
                question=data["question"]
            ).first()

            if existing:
                skipped_count += 1

                # Make sure career path is connected
                existing.career_paths.add(career)

                continue

            question = AssessmentQuestion.objects.create(
                question=data["question"],
                option_a=data["option_a"],
                option_b=data["option_b"],
                option_c=data["option_c"],
                option_d=data["option_d"],
                correct_answer=data["correct_answer"],
                category=data["category"],
                difficulty=data["difficulty"],
                skill=skill,
            )

            question.career_paths.add(career)

            added_count += 1

        # ---------------------------------------------------------
        # FINAL MESSAGE
        # ---------------------------------------------------------

        self.stdout.write(
            self.style.SUCCESS(
                f"Added: {added_count} questions"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Skipped existing: {skipped_count} questions"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Python Developer assessment import completed!"
            )
        )