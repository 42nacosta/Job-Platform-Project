# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

class Profile(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        RECRUITERS = "RECRUITERS", "Recruiters only"
        PRIVATE = "PRIVATE", "Private"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_recruiter = models.BooleanField(default=False)

    # Global visibility control
    visibility = models.CharField(
        max_length=12, choices=Visibility.choices, default=Visibility.RECRUITERS
    )

    # Field-level recruiter toggles (privacy-first defaults)
    show_email_to_recruiters = models.BooleanField(default=False)
    show_phone_to_recruiters = models.BooleanField(default=False)
    show_resume_to_recruiters = models.BooleanField(default=False)
    show_education_to_recruiters = models.BooleanField(default=False)
    show_experience_to_recruiters = models.BooleanField(default=False)
    show_location_to_recruiters = models.BooleanField(default = False)
    show_skills_to_recruiters = models.BooleanField(default = False)
    show_projects_to_recruiters = models.BooleanField(default = False)
    show_firstName_to_recruiters = models.BooleanField(default = False)
    show_lastName_to_recruiters = models.BooleanField(default = False)

    # Minimal profile data placeholders (extend later)
    headline = models.CharField(max_length=120, blank=True)
    email = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    education = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    resume_url = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    projects = models.TextField(blank=True, null=True)
    firstName = models.CharField(max_length=30, blank=True, null=True)
    lastName = models.CharField(max_length=30, blank=True, null=True)

    #users last action
    last_active = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {'Recruiter' if self.is_recruiter else 'Candidate'}"

    # Simple policy helper
    def can_view(self, viewer, field_key: str) -> bool:
        # Owner/Admin always see all fields
        if viewer and (viewer == self.user or viewer.is_staff):
            return True

        # Enforce global visibility first
        if self.visibility == self.Visibility.PRIVATE:
            return False

        is_viewer_recruiter = bool(getattr(getattr(viewer, "profile", None), "is_recruiter", False))

        if self.visibility == self.Visibility.RECRUITERS:
            if not is_viewer_recruiter:
                return False

        # Only recruiter-visible fields are governed by toggles
        sensitive = {"firstName", "lastName", "email", "phone", "resume", "education", "experience", "locations", "skills", "projects"}
        if field_key in sensitive:
            if is_viewer_recruiter:
                return getattr(self, f"show_{field_key}_to_recruiters", False)
            # Non-recruiters never see sensitive details
            return False

        # Non-sensitive fields (e.g., headline) are fine unless PRIVATE
        return True

def is_recruiter_property(self):
    return hasattr(self, "profile") and self.profile.is_recruiter
    
User.add_to_class("is_recruiter", property(is_recruiter_property))

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance,
            firstName=instance.first_name,
            lastName=instance.last_name,
            email=instance.email,)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    # Ensures profile exists even if superuser created via shell
    Profile.objects.get_or_create(user=instance)

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)  # ✅ created automatically when saved

    def __str__(self):
        return f"{self.user.username} - {self.action} ({self.timestamp:%Y-%m-%d %H:%M:%S})"