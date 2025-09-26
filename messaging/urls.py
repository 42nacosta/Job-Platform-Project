from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    path("inbox/", views.inbox, name="inbox"),
    path("app/<int:application_id>/", views.conversation_detail, name="conversation_detail"),
    path("app/<int:application_id>/send/", views.send_message, name="send_message"),
    path("user/<str:username>/", views.direct_conversation_detail, name="direct_conversation"),
    path("user/<str:username>/send/", views.send_direct_message, name="send_direct_message"),
]
