from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("privacy/", views.privacy_settings, name="privacy"),
    path("u/<str:username>/", views.profile_detail, name="profile_detail"),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
]
