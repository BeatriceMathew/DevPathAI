from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from ai_engine.services import generate_ai_roadmap


class Command(BaseCommand):

    help = "Test Gemini AI personalized roadmap generation"

    def handle(self, *args, **kwargs):

        username = input(
            "Enter the student username: "
        ).strip()

        try:

            user = User.objects.get(
                username=username
            )

        except User.DoesNotExist:

            self.stdout.write(
                self.style.ERROR(
                    f"User '{username}' does not exist."
                )
            )

            return

        self.stdout.write(
            "\nGenerating personalized roadmap..."
        )

        try:

            roadmap = generate_ai_roadmap(
                user
            )

        except Exception as e:

            self.stdout.write(
                self.style.ERROR(
                    f"\nAI generation failed:\n{e}"
                )
            )

            return

        self.stdout.write(
            self.style.SUCCESS(
                "\nAI roadmap generated successfully!\n"
            )
        )

        import json

        print(
            json.dumps(
                roadmap,
                indent=4,
                ensure_ascii=False
            )
        )