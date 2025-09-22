from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_recruiter", "visibility")
    list_filter = ("is_recruiter", "visibility")
    search_fields = ("user__username", "user__email")