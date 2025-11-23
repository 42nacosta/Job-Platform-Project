from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import requests
from django.conf import settings

# Create your models here.
class Job(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default="")
    description = models.TextField(max_length=1023, default="")
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    location = models.TextField(max_length=128, default="")
    category = models.TextField(max_length=128, default="")
    #extra info for map api
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return str(self.id) + ' - ' + self.title

class Application(models.Model):
    class Status(models.TextChoices):
        SUBMITTED   = "SUBMITTED", "Submitted"
        SCREENING   = "SCREENING", "Screening"
        INTERVIEW   = "INTERVIEW", "Interview"
        OFFER       = "OFFER",     "Offer"
        HIRED       = "HIRED",     "Hired"
        REJECTED    = "REJECTED",  "Rejected"
        WITHDRAWN   = "WITHDRAWN", "Withdrawn"

    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    note = models.TextField(max_length=500, blank=True, default="")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUBMITTED, db_index=True,)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # map clustering fields
    applicant_location = models.CharField(max_length=100, blank=True, default="")
    applicant_lat = models.FloatField(null=True, blank=True)
    applicant_lng = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("job", "applicant")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title}"


# PSEUDOCODE: CandidateRecommendation links a Job to a candidate Profile with match score
# Used by recruiters to discover qualified applicants based on skills/location matching
# Interacts with: Job (the posting), Profile (via user FK), recommendations.py (scoring engine)
class CandidateRecommendation(models.Model):
    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="candidate_recommendations")
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recommended_for_jobs")
    match_score = models.IntegerField(default=0)  # 0-100 score
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("job", "candidate")
        ordering = ["-match_score", "-created_at"]
        indexes = [
            models.Index(fields=["job", "-match_score"]),
            models.Index(fields=["candidate"]),
        ]

    def __str__(self):
        return f"{self.candidate.username} recommended for {self.job.title} ({self.match_score}%)"


# PSEUDOCODE: JobRecommendation links a candidate Profile to a Job with match score
# Used by job seekers to discover relevant opportunities based on their skills/location
# Interacts with: Profile (via user FK), Job (the posting), recommendations.py (scoring engine)
class JobRecommendation(models.Model):
    id = models.AutoField(primary_key=True)
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name="job_recommendations")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="recommended_to_candidates")
    match_score = models.IntegerField(default=0)  # 0-100 score
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("candidate", "job")
        ordering = ["-match_score", "-created_at"]
        indexes = [
            models.Index(fields=["candidate", "-match_score"]),
            models.Index(fields=["job"]),
        ]

    def __str__(self):
        return f"{self.job.title} recommended to {self.candidate.username} ({self.match_score}%)"

class SavedCandidateSearch(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_candidate_searches")
    name = models.CharField(max_length=120)
    keywords = models.CharField(max_length=255, blank=True, help_text="Search text across headline/skills/projects")
    location = models.CharField(max_length=255, blank=True)
    min_years_experience = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["owner", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class SavedCandidateMatch(models.Model):
    search = models.ForeignKey(SavedCandidateSearch, on_delete=models.CASCADE, related_name="matches")
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_search_hits")
    matched_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    class Meta:
        unique_together = ("search", "candidate")
        ordering = ["-matched_at"]
        indexes = [
            models.Index(fields=["search", "seen", "-matched_at"]),
        ]

    def __str__(self):
        return f"{self.search.name} -> {self.candidate.username}"




def geocode_location(address):
    api_key = settings.GOOGLE_MAPS_API_KEY
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"
    response = requests.get(url).json()

    if response['status'] == 'OK':
        location = response['results'][0]['geometry']['location']
        return location['lat'], location['lng']
    return None, None