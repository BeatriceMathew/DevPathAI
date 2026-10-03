from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
import re


class RegisterForm(UserCreationForm):

    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your first name"
        })
    )

    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your last name"
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your email address"
        })
    )

    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Choose a username"
        })
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Create a password"
        }),
        required=True
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Confirm your password"
        }),
        required=True
    )


    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "username",
            "password1",
            "password2"
        ]


    # -----------------------------
    # FIRST NAME
    # -----------------------------

    def clean_first_name(self):

        first_name = self.cleaned_data.get("first_name").strip()

        if len(first_name) < 2:
            raise forms.ValidationError(
                "First name must contain at least 2 characters."
            )

        if not re.fullmatch(r"[A-Za-z ]+", first_name):
            raise forms.ValidationError(
                "First name can contain letters only."
            )

        return first_name


    # -----------------------------
    # LAST NAME
    # -----------------------------

    def clean_last_name(self):

        last_name = self.cleaned_data.get("last_name").strip()

        if len(last_name) < 2:
            raise forms.ValidationError(
                "Last name must contain at least 2 characters."
            )

        if not re.fullmatch(r"[A-Za-z ]+", last_name):
            raise forms.ValidationError(
                "Last name can contain letters only."
            )

        return last_name


    # -----------------------------
    # EMAIL
    # -----------------------------

    def clean_email(self):

        email = self.cleaned_data.get("email").strip().lower()

        if not email:
            raise forms.ValidationError(
                "Email address is required."
            )

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email


    # -----------------------------
    # USERNAME
    # -----------------------------

    def clean_username(self):

        username = self.cleaned_data.get("username").strip()

        if len(username) < 3:
            raise forms.ValidationError(
                "Username must contain at least 3 characters."
            )

        if not re.fullmatch(r"[A-Za-z0-9_]+", username):
            raise forms.ValidationError(
                "Username can contain only letters, numbers and underscore."
            )

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username


    # -----------------------------
    # PASSWORD
    # -----------------------------

    def clean_password1(self):

        password = self.cleaned_data.get("password1")

        if len(password) < 8:
            raise forms.ValidationError(
                "Password must contain at least 8 characters."
            )

        if not re.search(r"[A-Z]", password):
            raise forms.ValidationError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r"[a-z]", password):
            raise forms.ValidationError(
                "Password must contain at least one lowercase letter."
            )

        if not re.search(r"[0-9]", password):
            raise forms.ValidationError(
                "Password must contain at least one number."
            )

        if not re.search(r"[^A-Za-z0-9]", password):
            raise forms.ValidationError(
                "Password must contain at least one special character."
            )

        return password



class EditProfileForm(forms.ModelForm):

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
        ]

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "placeholder": "Enter username",
                    "class": "form-control",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Enter email address",
                    "class": "form-control",
                }
            ),

            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter first name",
                    "class": "form-control",
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter last name",
                    "class": "form-control",
                }
            ),
        }

    # -----------------------------
    # Username validation
    # -----------------------------
    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()

        if not username:
            raise forms.ValidationError("Username is required.")

        if len(username) < 3:
            raise forms.ValidationError(
                "Username must contain at least 3 characters."
            )

        if len(username) > 30:
            raise forms.ValidationError(
                "Username cannot exceed 30 characters."
            )

        if not re.match(r"^[A-Za-z0-9_]+$", username):
            raise forms.ValidationError(
                "Username can contain only letters, numbers and underscore."
            )

        # Check duplicate username, excluding current user
        if User.objects.filter(
            username__iexact=username
        ).exclude(pk=self.instance.pk).exists():

            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    # -----------------------------
    # Email validation
    # -----------------------------
    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()

        if not email:
            raise forms.ValidationError("Email address is required.")

        # Basic email format validation
        email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

        if not re.match(email_pattern, email):
            raise forms.ValidationError(
                "Enter a valid email address."
            )

        # Check duplicate email
        if User.objects.filter(
            email__iexact=email
        ).exclude(pk=self.instance.pk).exists():

            raise forms.ValidationError(
                "This email address is already registered."
            )

        return email

    # -----------------------------
    # First name validation
    # -----------------------------
    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name", "").strip()

        if not first_name:
            raise forms.ValidationError(
                "First name is required."
            )

        if len(first_name) < 2:
            raise forms.ValidationError(
                "First name must contain at least 2 characters."
            )

        if len(first_name) > 50:
            raise forms.ValidationError(
                "First name cannot exceed 50 characters."
            )

        if not re.match(r"^[A-Za-z ]+$", first_name):
            raise forms.ValidationError(
                "First name can contain only letters and spaces."
            )

        return first_name

    # -----------------------------
    # Last name validation
    # -----------------------------
    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name", "").strip()

        if not last_name:
            raise forms.ValidationError(
                "Last name is required."
            )

        if len(last_name) < 2:
            raise forms.ValidationError(
                "Last name must contain at least 2 characters."
            )

        if len(last_name) > 50:
            raise forms.ValidationError(
                "Last name cannot exceed 50 characters."
            )

        if not re.match(r"^[A-Za-z ]+$", last_name):
            raise forms.ValidationError(
                "Last name can contain only letters and spaces."
            )

        return last_name