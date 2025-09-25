from django.contrib.auth.forms import UserCreationForm
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from django import forms
from .models import Profile
from django.contrib.auth.models import User


class CustomErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return mark_safe(''.join([f'<div class="alert alert-danger" role="alert">{e}</div>' for e in self]))

class CustomUserCreationForm(UserCreationForm):
    is_recruiter = forms.BooleanField(
        required=False,
        label="Are you a recruiter?",
        help_text=None,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "is_recruiter")
    
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'password1',
        'password2']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update(
                {'class': 'form-control'}
            )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_recruiter = self.cleaned_data.get("is_recruiter", False)
        if commit:
            user.save()
        return user

class PrivacySettingsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "visibility",
            "show_email_to_recruiters",
            "show_phone_to_recruiters",
            "show_resume_to_recruiters",
            "show_education_to_recruiters",
            "show_experience_to_recruiters",
            "phone",
            "education",
            "experience",
            "resume_url",
        )
        widgets = {
            "visibility": forms.RadioSelect,
        }
        labels = {
            "visibility": "Who can view my profile?",
            "show_email_to_recruiters": "Show my email to recruiters",
            "show_phone_to_recruiters": "Show my phone to recruiters",
            "show_resume_to_recruiters": "Show my resume link to recruiters",
            "show_education_to_recruiters": "Show education to recruiters",
            "show_experience_to_recruiters": "Show experience to recruiters",
        }