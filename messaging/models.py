from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from home.models import Application

class Conversation(models.Model):
    application = models.OneToOneField(
        Application, on_delete=models.CASCADE, related_name="conversation"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def participants(self):
        return [self.application.job.user, self.application.applicant]

    def __str__(self):
        a = self.application
        return f"Conversation: {a.applicant.username} ↔ {a.job.title}"

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def mark_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=["read_at"])

class DirectConversation(models.Model):
    user_one = models.ForeignKey(User, on_delete=models.CASCADE, related_name="direct_as_one")
    user_two = models.ForeignKey(User, on_delete=models.CASCADE, related_name="direct_as_two")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user_one", "user_two"]),
        ]
        # we’ll canonicalize ordering (smaller id = user_one) to avoid duplicates

    def participants(self):
        return [self.user_one, self.user_two]

    def __str__(self):
        return f"Direct: {self.user_one.username} ↔ {self.user_two.username}"

class DirectMessage(models.Model):
    conversation = models.ForeignKey(DirectConversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def mark_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=["read_at"])
