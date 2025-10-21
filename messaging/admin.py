from django.contrib import admin
from .models import Conversation, Message, DirectConversation, DirectMessage

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "created_at")
    search_fields = ("application__job__title", "application__applicant__username")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "created_at", "read_at")
    list_filter = ("read_at", "created_at")
    search_fields = ("body", "sender__username")

@admin.register(DirectConversation)
class DirectConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user_one", "user_two", "created_at")
    search_fields = ("user_one__username", "user_two__username")

@admin.register(DirectMessage)
class DirectMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "created_at", "read_at")
    list_filter = ("created_at", "read_at")
    search_fields = ("sender__username", "conversation__user_one__username", "conversation__user_two__username", "body")