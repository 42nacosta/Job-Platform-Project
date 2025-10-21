from django.contrib import admin
from django.http import HttpResponse
from .models import Profile, UserActivity
import csv


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "is_recruiter", "visibility", "last_active")
    list_filter = ("is_recruiter", "visibility")
    search_fields = ("user__username", "user__email", "firstName", "lastName")

    actions = ["export_profiles_csv"]

    def export_profiles_csv(self, request, queryset):
        from django.utils.timezone import localtime
        queryset = queryset.select_related("user")

        response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
        response["Content-Disposition"] = 'attachment; filename="profiles_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Username", "First Name", "Last Name", "Email",
            "Is Recruiter", "Visibility", "Last Active",
        ])

        user_ids = [p.user_id for p in queryset]
        activities = (
            UserActivity.objects
            .filter(user_id__in=user_ids)
            .order_by("user_id", "-timestamp")
        )

        last_activities = {}
        for activity in activities:
            if activity.user_id not in last_activities:
                last_activities[activity.user_id] = activity

        for profile in queryset:
            last_activity = last_activities.get(profile.user_id)

            writer.writerow([
                profile.user.username,
                profile.firstName or "",
                profile.lastName or "",
                profile.user.email,
                "Yes" if profile.is_recruiter else "No",
                profile.visibility,
                localtime(profile.last_active).strftime("%Y-%m-%d %H:%M:%S") if profile.last_active else "N/A",
            ])

        UserActivity.objects.create(
            user=request.user,
            action=f"Exported {queryset.count()} profiles with activity data"
        )

        self.message_user(
            request,
            f"Exported {queryset.count()} profiles with timestamps to CSV.",
            level="info"
        )
        return response