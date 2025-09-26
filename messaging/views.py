from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone

from home.models import Application
from .models import Conversation, Message

from django.contrib.auth.models import User
from .models import DirectConversation, DirectMessage



def _can_access(user, application):
    # Only recruiter (job owner) or candidate (applicant) can access messages for this application
    return user.is_authenticated and user in (application.job.user, application.applicant)

def _get_or_create_conversation(application):
    conv, _ = Conversation.objects.get_or_create(application=application)
    return conv


@login_required
def conversation_detail(request, application_id):
    application = get_object_or_404(
        Application.objects.select_related("job", "applicant"),
        id=application_id
    )
    if not _can_access(request.user, application):
        return HttpResponseForbidden("Not allowed")

    conv = _get_or_create_conversation(application)

    # mark the other side's unread messages as read
    Message.objects.filter(conversation=conv) \
        .exclude(sender=request.user) \
        .filter(read_at__isnull=True) \
        .update(read_at=timezone.now())

    return render(request, "messaging/conversation.html", {"conv": conv, "application": application})


@login_required
@require_POST
def send_message(request, application_id):
    application = get_object_or_404(
        Application.objects.select_related("job", "applicant"),
        id=application_id
    )
    if not _can_access(request.user, application):
        return HttpResponseForbidden("Not allowed")

    body = (request.POST.get("body") or "").strip()
    if body:
        conv = _get_or_create_conversation(application)
        Message.objects.create(conversation=conv, sender=request.user, body=body[:2000])

    return redirect("messaging:conversation_detail", application_id=application.id)

def _canonical_pair(u1, u2):
    # Ensure consistent ordering so we don't create duplicates
    return (u1, u2) if u1.id < u2.id else (u2, u1)

def _get_or_create_direct_conv(u_current, u_other):
    a, b = _canonical_pair(u_current, u_other)
    conv, _ = DirectConversation.objects.get_or_create(user_one=a, user_two=b)
    return conv

def _can_access_direct(user, conv: DirectConversation):
    return user.is_authenticated and user in (conv.user_one, conv.user_two)

@login_required
def direct_conversation_detail(request, username):
    other = get_object_or_404(User, username=username)
    conv = _get_or_create_direct_conv(request.user, other)

    # mark unread as read
    DirectMessage.objects.filter(conversation=conv).exclude(sender=request.user)\
        .filter(read_at__isnull=True).update(read_at=timezone.now())

    return render(request, "messaging/direct_conversation.html",
                  {"conv": conv, "other": other})

@login_required
@require_POST
def send_direct_message(request, username):
    other = get_object_or_404(User, username=username)
    conv = _get_or_create_direct_conv(request.user, other)
    body = (request.POST.get("body") or "").strip()
    if body:
        DirectMessage.objects.create(conversation=conv, sender=request.user, body=body[:2000])
    return redirect("messaging:direct_conversation", username=other.username)

@login_required
def inbox(request):
    apps = Application.objects.filter(
        models.Q(applicant=request.user) | models.Q(job__user=request.user)
    ).select_related("job", "applicant")
    convs = Conversation.objects.filter(application__in=apps).select_related(
        "application__job", "application__applicant"
    )

    # Direct conversations
    direct_convs = DirectConversation.objects.filter(
        models.Q(user_one=request.user) | models.Q(user_two=request.user)
    ).select_related("user_one", "user_two")

    return render(
        request,
        "messaging/inbox.html",
        {"conversations": convs, "direct_conversations": direct_convs}
    )
