from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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

    def __str__(self):
        return str(self.id) + ' - ' + self.title


class Application(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    id = models.AutoField(primary_key=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    note = models.TextField(max_length=500, blank=True, default="")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("job", "applicant")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.applicant.username} -> {self.job.title}"
