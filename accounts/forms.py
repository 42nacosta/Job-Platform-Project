from django.contrib.auth.forms import UserCreationForm
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from django import forms
from django.core.validators import RegexValidator
from .models import Profile
from django.contrib.auth.models import User


class CustomErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return mark_safe(''.join([f'<div class="alert alert-danger" role="alert">{e}</div>' for e in self]))

class CustomUserCreationForm(UserCreationForm):
    firstName = forms.CharField(
        max_length=30,
        required=True,
        label="First Name",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    lastName = forms.CharField(
        max_length=30,
        required=True,
        label="Last Name",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.CharField(
        max_length=30,
        required=True,
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    ROLE_CHOICES = [
        (False, 'Job Seeker - Looking for opportunities'),
        (True, 'Recruiter - Posting jobs and hiring'),
    ]

    is_recruiter = forms.TypedChoiceField(
        required=True,
        label="I am a",
        choices=ROLE_CHOICES,
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial=False
    )

    class Meta:
        model = User
        fields = ("firstName", "lastName", "username", "email", "password1", "password2", "is_recruiter")
    
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["firstName"]
        user.last_name = self.cleaned_data["lastName"]
        user.email = self.cleaned_data["email"]

        if commit:
            user.save()
            user.profile.is_recruiter = self.cleaned_data.get("is_recruiter", False)
            user.profile.save()
        return user

class PrivacySettingsForm(forms.ModelForm):
    phone = forms.CharField(
        required=False,
        max_length=30,
        validators=[RegexValidator(r"^\d*$", "Enter numbers only.")],
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "inputmode": "numeric",
                "pattern": "[0-9]*",
                "placeholder": "Digits only",
            }
        ),
    )

    class Meta:
        model = Profile
        fields = (
            "visibility",
            "show_email_to_recruiters",
            "show_phone_to_recruiters",
            "show_resume_to_recruiters",
            "show_education_to_recruiters",
            "show_experience_to_recruiters",
            "show_location_to_recruiters",
            "show_skills_to_recruiters",
            "show_projects_to_recruiters",
            "show_firstName_to_recruiters",
            "show_lastName_to_recruiters",
            "phone",
            "education",
            "experience",
            "resume_url",
            "location",
            "skills",
            "projects",
            "firstName",
            "lastName",
            "email", 
        )
        widgets = {
            "visibility": forms.RadioSelect(attrs={"class": "form-check-input"}),
            "education": forms.Textarea(attrs={"rows": 3}),
            "experience": forms.Textarea(attrs={"rows": 3}),
            "skills": forms.Textarea(attrs={"rows": 3}),
            "projects": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "visibility": "Who can view my profile?",
            "show_email_to_recruiters": "Show my email to recruiters",
            "show_phone_to_recruiters": "Show my phone to recruiters",
            "show_resume_to_recruiters": "Show my resume link to recruiters",
            "show_education_to_recruiters": "Show education to recruiters",
            "show_experience_to_recruiters": "Show experience to recruiters",
            "show_location_to_recruiters": "Show location to recruiters",
            "show_skills_to_recruiters" : "Show skills to recruiters",
            "show_projects_to_recruiters" : "Show projects to recruiters",
            "show_firstName_to_recruiters" : "Show first name to recruiters",
            "show_lastName_to_recruiters" : "Show last name to recruiters",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        checkbox_fields = [
            "show_email_to_recruiters",
            "show_phone_to_recruiters",
            "show_resume_to_recruiters",
            "show_education_to_recruiters",
            "show_experience_to_recruiters",
            "show_location_to_recruiters",
            "show_skills_to_recruiters",
            "show_projects_to_recruiters",
            "show_firstName_to_recruiters",
            "show_lastName_to_recruiters",
        ]

        for name, field in self.fields.items():
            widget = field.widget
            if name in checkbox_fields and isinstance(widget, forms.CheckboxInput):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} form-check-input".strip()
            elif isinstance(widget, (forms.TextInput, forms.EmailInput, forms.URLInput, forms.Textarea)):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} form-control".strip()
            elif isinstance(widget, forms.RadioSelect):
                widget.attrs["class"] = "form-check-input"

        self.fields["email"].widget.attrs.setdefault("placeholder", "name@example.com")
        self.fields["resume_url"].widget.attrs.setdefault("placeholder", "https://...")
